"""Flask dashboard application and REST API routes for local monitoring."""

from __future__ import annotations

import os
import secrets
import time
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, send_file

from app.config import get_settings
from app.database.db import get_connection, transaction
from app.leads.exporter import export_leads_to_excel
from app.leads.repository import LeadRepository
from app.logging import get_logger

log = get_logger("app.dashboard")

# Short-lived CSRF state values for the Gmail OAuth handshake.
_PENDING_STATES: dict[str, float] = {}
_STATE_TTL_SECONDS = 600.0


def _issue_state() -> str:
    """Create a one-time CSRF state token for the OAuth redirect."""
    now = time.time()
    for key, created in list(_PENDING_STATES.items()):
        if now - created > _STATE_TTL_SECONDS:
            del _PENDING_STATES[key]
    state = secrets.token_urlsafe(24)
    _PENDING_STATES[state] = now
    return state


def _consume_state(state: str) -> bool:
    """Validate and immediately invalidate a state token (single use)."""
    created = _PENDING_STATES.pop(state, None)
    if created is None:
        return False
    return (time.time() - created) <= _STATE_TTL_SECONDS


def _set_connection(service: str, status: str, account: str | None, error: str | None) -> None:
    """Update a connection row and stamp the last test time."""
    with transaction() as tx:
        tx.execute(
            "UPDATE connections SET status = ?, account_identifier = ?, "
            "last_tested_at = CURRENT_TIMESTAMP, error_message = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE service = ?;",
            (status, account, error, service),
        )


def _log_event(event_type: str, message: str, icon: str, status: str) -> None:
    """Append an entry to the dashboard activity stream."""
    with transaction() as tx:
        tx.execute(
            "INSERT INTO events (event_type, message, icon, status) VALUES (?, ?, ?, ?);",
            (event_type, message, icon, status),
        )


def create_app() -> Flask:
    """Factory creating the Flask dashboard application."""
    template_folder = Path(__file__).parent / "templates"
    static_folder = Path(__file__).parent / "static"

    app = Flask(
        __name__,
        template_folder=str(template_folder),
        static_folder=str(static_folder),
    )
    app.config["SECRET_KEY"] = os.urandom(24)
    settings = get_settings()

    @app.route("/")
    def index():
        return render_template(
            "index.html", mode=settings.mode_label, dry_run=settings.dry_run
        )

    @app.route("/api/state", methods=["GET"])
    def get_state():
        repo = LeadRepository()
        counts = repo.get_summary_counts()
        conn = get_connection()

        # started_at has second resolution, so rowid breaks ties deterministically.
        run = conn.execute(
            "SELECT * FROM runs ORDER BY started_at DESC, rowid DESC LIMIT 1;"
        ).fetchone()

        total = counts["total"]
        completed = counts["completed"]
        progress_pct = round((completed / total * 100), 1) if total > 0 else 0.0

        connections = {
            row["service"]: {
                "status": row["status"],
                "account": row["account_identifier"],
                "provider": row["provider"],
            }
            for row in conn.execute(
                "SELECT service, status, account_identifier, provider FROM connections;"
            ).fetchall()
        }

        return jsonify({
            "mode": settings.mode_label,
            "dry_run": settings.dry_run,
            "run_status": run["status"] if run else "READY",
            "current_action": run["current_action"] if run else "Idle",
            "current_lead": run["current_lead_name"] if run else None,
            "progress_percent": progress_pct,
            "metrics": {
                "total": total,
                "completed": completed,
                "pending": counts["pending"],
                "failed": counts["failed"],
                "priority": counts["priority"],
                "email_sent": counts["email_sent"],
                "whatsapp_sent": counts["whatsapp_sent"],
                "opted_out": counts["opted_out"],
            },
            "connections": connections,
        })

    @app.route("/api/leads", methods=["GET"])
    def list_leads():
        conn = get_connection()
        priority_only = request.args.get("priority", "false").lower() == "true"
        query = "SELECT * FROM leads"
        params: list[Any] = []
        if priority_only:
            query += " WHERE is_priority = 1"
        query += " ORDER BY is_priority DESC, created_at ASC LIMIT 100;"
        rows = conn.execute(query, params).fetchall()
        return jsonify({"leads": [dict(r) for r in rows], "count": len(rows)})

    @app.route("/api/events", methods=["GET"])
    def list_events():
        limit = int(request.args.get("limit", 50))
        rows = get_connection().execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?;", (limit,)
        ).fetchall()
        return jsonify({"events": [dict(r) for r in rows]})
    @app.route("/api/control", methods=["POST"])
    def control_action():
        data = request.get_json() or {}
        action = data.get("action", "").lower()
        if action not in {"start", "pause", "resume", "stop"}:
            return jsonify({"error": f"Invalid action: {action}"}), 400

        conn = get_connection()
        with transaction() as tx:
            if action == "start":
                # Reuse the active run if one exists, otherwise create a new one.
                active = tx.execute(
                    "SELECT id FROM runs WHERE status IN ('RUNNING', 'PAUSED') "
                    "ORDER BY started_at DESC, rowid DESC LIMIT 1;"
                ).fetchone()
                if active:
                    tx.execute(
                        "UPDATE runs SET status = 'RUNNING', ended_at = NULL, "
                        "current_action = 'Campaign started' WHERE id = ?;",
                        (active["id"],),
                    )
                else:
                    tx.execute(
                        """
                        INSERT INTO runs (id, status, mode, current_action, total_leads)
                        VALUES ('run-' || lower(hex(randomblob(4))), 'RUNNING', ?,
                                'Campaign started', (SELECT COUNT(*) FROM leads));
                        """,
                        (settings.mode_label,),
                    )
                tx.execute(
                    "INSERT INTO events (event_type, message, icon, status) "
                    "VALUES ('CAMPAIGN_STARTED', 'Outreach campaign initiated from dashboard', '→', 'INFO');"
                )
            elif action == "pause":
                tx.execute(
                    "UPDATE runs SET status = 'PAUSED', current_action = 'Paused by operator' "
                    "WHERE status = 'RUNNING';"
                )
                tx.execute(
                    "INSERT INTO events (event_type, message, icon, status) "
                    "VALUES ('CAMPAIGN_PAUSED', 'Operator paused campaign', '○', 'INFO');"
                )
            elif action == "resume":
                tx.execute(
                    "UPDATE runs SET status = 'RUNNING', current_action = 'Resumed by operator' "
                    "WHERE status = 'PAUSED';"
                )
                tx.execute(
                    "INSERT INTO events (event_type, message, icon, status) "
                    "VALUES ('CAMPAIGN_RESUMED', 'Operator resumed campaign', '→', 'INFO');"
                )
            elif action == "stop":
                tx.execute(
                    "UPDATE runs SET status = 'STOPPED', current_action = 'Stopped by operator', "
                    "ended_at = CURRENT_TIMESTAMP WHERE status IN ('RUNNING', 'PAUSED');"
                )
                tx.execute(
                    "INSERT INTO events (event_type, message, icon, status) "
                    "VALUES ('CAMPAIGN_STOPPED', 'Operator stopped campaign', '✕', 'WARNING');"
                )

        return jsonify({"status": "ok", "action": action})

    # ------------------------------------------------------------------
    # Gmail OAuth 2.0 (installed-app loopback flow)
    # ------------------------------------------------------------------

    @app.route("/api/connections/gmail", methods=["GET"])
    def gmail_status():
        """Report OAuth client configuration and authorization state."""
        from app.integrations.gmail import oauth

        status = oauth.verify_connection()
        _set_connection(
            "gmail",
            "CONNECTED" if status.authorized else "DISCONNECTED",
            status.account_email,
            None if status.authorized else status.detail,
        )
        return jsonify({
            "client": oauth.client_summary(),
            "authorized": status.authorized,
            "account": status.account_email,
            "scopes": status.scopes,
            "detail": status.detail,
        })

    @app.route("/api/connections/gmail/connect", methods=["GET"])
    def gmail_connect():
        """Return the Google consent URL for the operator to open."""
        from app.integrations.gmail import oauth

        redirect_uri = request.url_root.rstrip("/") + "/oauth2/callback"
        state = _issue_state()
        try:
            url = oauth.build_authorization_url(state, redirect_uri)
        except oauth.GmailAuthError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"authorization_url": url, "state": state})
    @app.route("/api/connections/whatsapp", methods=["GET"])
    def whatsapp_status():
        """Describe the current WhatsApp connection (never exposes the token)."""
        from app.integrations.whatsapp import service

        return jsonify(service.connection_info().to_dict())

    @app.route("/api/connections/whatsapp/connect", methods=["POST"])
    def whatsapp_connect():
        """Store Meta credentials, run a live test, persist the result."""
        from app.integrations.whatsapp import service

        data = request.get_json() or {}
        phone_number_id = str(data.get("phone_number_id", "")).strip()
        waba_id = str(data.get("waba_id", "")).strip()
        access_token = str(data.get("access_token", "")).strip()

        if not phone_number_id or not access_token:
            return jsonify({
                "error": "phone_number_id and access_token are required.",
                "hint": "Find these in Meta Business Manager > WhatsApp > API Setup.",
            }), 400

        outcome = service.connect_whatsapp(phone_number_id, waba_id, access_token)
        result = outcome["result"]
        return jsonify({
            "storage": outcome["storage"],
            "connected": result.status.value == "SENT",
            "status": result.status.value,
            "detail": result.detail,
        })

    @app.route("/api/connections/whatsapp/test", methods=["POST"])
    def whatsapp_test():
        """Re-run the provider connection test on demand."""
        from app.integrations.whatsapp import service

        result = service.test_whatsapp_connection()
        ok = result.status.value == "SENT"
        _set_connection("whatsapp", "CONNECTED" if ok else "DISCONNECTED",
                        result.detail[:120] if ok else None, None if ok else result.detail)
        return jsonify({"ok": ok, "status": result.status.value, "detail": result.detail})

    @app.route("/api/connections/whatsapp/disconnect", methods=["POST"])
    def whatsapp_disconnect():
        """Remove stored Meta credentials."""
        from app.integrations.whatsapp import service

        removed = service.disconnect_whatsapp()
        return jsonify({"status": "disconnected", "credentials_removed": removed})

    @app.route("/api/export", methods=["GET"])
    def export_excel():
        out_file = settings.data_dir / "exports" / "leads_export.xlsx"
        export_leads_to_excel(out_file)
        return send_file(
            str(out_file),
            as_attachment=True,
            download_name="d_web_studio_leads_export.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @app.route("/oauth2/callback", methods=["GET"])
    def gmail_callback():
        """Google redirects here with ?code=...&state=... after consent."""
        from app.integrations.gmail import oauth

        code = request.args.get("code")
        state = request.args.get("state", "")
        error = request.args.get("error")

        if error:
            log.warning("Operator denied Gmail consent: %s", error)
            return redirect("/?gmail=denied")
        if not code:
            return redirect("/?gmail=missing_code")
        if not _consume_state(state):
            log.warning("Gmail callback rejected: invalid or expired state token.")
            return redirect("/?gmail=bad_state")

        redirect_uri = request.url_root.rstrip("/") + "/oauth2/callback"
        try:
            creds = oauth.exchange_code(code, redirect_uri)
        except Exception as exc:  # noqa: BLE001
            log.error("Gmail token exchange failed: %s", exc)
            return redirect("/?gmail=error")
        if not creds or not creds.token:
            return redirect("/?gmail=error")

        status = oauth.verify_connection()
        _set_connection(
            "gmail",
            "CONNECTED" if status.authorized else "ERROR",
            status.account_email,
            None if status.authorized else status.detail,
        )
        _log_event("GMAIL_CONNECTED", f"Gmail connected: {status.account_email}", "✓", "SUCCESS")
        return redirect("/?gmail=connected")

    @app.route("/api/connections/gmail/test", methods=["POST"])
    def gmail_test():
        """Interactive connection test against the live Gmail API."""
        from app.integrations.gmail import oauth

        status = oauth.verify_connection()
        _set_connection(
            "gmail",
            "CONNECTED" if status.authorized else "DISCONNECTED",
            status.account_email,
            None if status.authorized else status.detail,
        )
        return jsonify({
            "ok": status.authorized,
            "account": status.account_email,
            "detail": status.detail,
        })

    @app.route("/api/connections/gmail/disconnect", methods=["POST"])
    def gmail_disconnect():
        """Remove the stored token and mark the connection disconnected."""
        from app.integrations.gmail import oauth

        removed = oauth.revoke_local_token()
        _set_connection("gmail", "DISCONNECTED", None, None)
        _log_event("GMAIL_DISCONNECTED", "Gmail token removed locally", "✕", "WARNING")
        return jsonify({"status": "disconnected", "token_removed": removed})

    @app.route("/api/email/preview", methods=["POST"])
    def email_preview():
        """Validate and preview a message WITHOUT sending anything."""
        from app.integrations.gmail.message import MessageValidationError, build_email

        data = request.get_json() or {}
        try:
            built = build_email(
                to=data.get("to", ""),
                subject=data.get("subject", ""),
                body=data.get("body", ""),
                sender_name=settings.gmail_sender_name,
                sender_email=settings.gmail_sender_email or None,
            )
        except MessageValidationError as exc:
            return jsonify({"valid": False, "error": str(exc)}), 400
        return jsonify({
            "valid": True,
            "to": built.to,
            "subject": built.subject,
            "body": built.body,
            "dry_run": settings.dry_run,
        })
    return app
