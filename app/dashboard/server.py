"""Flask dashboard application and REST API routes for local monitoring."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_file

from app.config import get_settings
from app.database.db import get_connection, transaction
from app.leads.exporter import export_leads_to_excel
from app.leads.repository import LeadRepository
from app.logging import get_logger

log = get_logger("app.dashboard")


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
        return render_template("index.html", mode=settings.mode_label, dry_run=settings.dry_run)

    @app.route("/api/state", methods=["GET"])
    def get_state():
        repo = LeadRepository()
        counts = repo.get_summary_counts()
        conn = get_connection()

        # Fetch latest active or recent run.
        # started_at has second-level resolution, so rowid breaks ties deterministically.
        run = conn.execute(
            "SELECT * FROM runs ORDER BY started_at DESC, rowid DESC LIMIT 1;"
        ).fetchone()

        run_status = run["status"] if run else "READY"
        current_action = run["current_action"] if run else "Idle"
        current_lead = run["current_lead_name"] if run else None

        total = counts["total"]
        completed = counts["completed"]
        failed = counts["failed"]
        pending = counts["pending"]
        progress_pct = round((completed / total * 100), 1) if total > 0 else 0.0

        # Fetch connection statuses
        connections = {}
        for row in conn.execute("SELECT service, status, account_identifier FROM connections;").fetchall():
            connections[row["service"]] = {
                "status": row["status"],
                "account": row["account_identifier"],
            }

        return jsonify({
            "mode": settings.mode_label,
            "dry_run": settings.dry_run,
            "run_status": run_status,
            "current_action": current_action,
            "current_lead": current_lead,
            "progress_percent": progress_pct,
            "metrics": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "failed": failed,
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
        leads = [dict(r) for r in rows]
        return jsonify({"leads": leads, "count": len(leads)})

    @app.route("/api/events", methods=["GET"])
    def list_events():
        limit = int(request.args.get("limit", 50))
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?;",
            (limit,),
        ).fetchall()
        events = [dict(r) for r in rows]
        return jsonify({"events": events})

    @app.route("/api/control", methods=["POST"])
    def control_action():
        data = request.get_json() or {}
        action = data.get("action", "").lower()
        if action not in {"start", "pause", "resume", "stop"}:
            return jsonify({"error": f"Invalid action: {action}"}), 400

        # Automation controller integration (invoked in Phase 5)
        # Updates runs record to signal the background worker
        conn = get_connection()
        with transaction():
            if action == "start":
                # Reuse the active run if one exists, otherwise create a new one.
                active = conn.execute(
                    "SELECT id FROM runs WHERE status IN ('RUNNING', 'PAUSED') "
                    "ORDER BY started_at DESC, rowid DESC LIMIT 1;"
                ).fetchone()
                if active:
                    conn.execute(
                        "UPDATE runs SET status = 'RUNNING', ended_at = NULL, "
                        "current_action = 'Campaign started' WHERE id = ?;",
                        (active["id"],),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO runs (id, status, mode, current_action, total_leads)
                        VALUES ('run-' || lower(hex(randomblob(4))), 'RUNNING', ?,
                                'Campaign started', (SELECT COUNT(*) FROM leads));
                        """,
                        (settings.mode_label,),
                    )
                conn.execute(
                    """
                    INSERT INTO events (event_type, message, icon, status)
                    VALUES ('CAMPAIGN_STARTED', 'Outreach campaign initiated from dashboard', '→', 'INFO');
                    """
                )
            elif action == "pause":
                conn.execute("UPDATE runs SET status = 'PAUSED', current_action = 'Paused by operator' WHERE status = 'RUNNING';")
                conn.execute("INSERT INTO events (event_type, message, icon, status) VALUES ('CAMPAIGN_PAUSED', 'Operator paused campaign', '○', 'INFO');")
            elif action == "resume":
                conn.execute("UPDATE runs SET status = 'RUNNING', current_action = 'Resumed by operator' WHERE status = 'PAUSED';")
                conn.execute("INSERT INTO events (event_type, message, icon, status) VALUES ('CAMPAIGN_RESUMED', 'Operator resumed campaign', '→', 'INFO');")
            elif action == "stop":
                conn.execute("UPDATE runs SET status = 'STOPPED', current_action = 'Stopped by operator', ended_at = CURRENT_TIMESTAMP WHERE status IN ('RUNNING', 'PAUSED');")
                conn.execute("INSERT INTO events (event_type, message, icon, status) VALUES ('CAMPAIGN_STOPPED', 'Operator stopped campaign', '✕', 'WARNING');")

        return jsonify({"status": "ok", "action": action})

    @app.route("/api/connections/whatsapp", methods=["POST"])
    def configure_whatsapp():
        """Update WhatsApp credentials securely."""
        data = request.get_json() or {}
        phone_number_id = str(data.get("phone_number_id", "")).strip()
        waba_id = str(data.get("waba_id", "")).strip()
        access_token = str(data.get("access_token", "")).strip()

        if not phone_number_id or not access_token:
            return jsonify({"error": "phone_number_id and access_token are required"}), 400

        conn = get_connection()
        with transaction():
            conn.execute(
                """
                INSERT INTO connections (id, service, provider, status, phone_number_id, business_account_id, updated_at)
                VALUES ('conn-whatsapp', 'whatsapp', 'meta_cloud', 'CONNECTED', ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(service) DO UPDATE SET
                    provider = 'meta_cloud',
                    status = 'CONNECTED',
                    phone_number_id = excluded.phone_number_id,
                    business_account_id = excluded.business_account_id,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (phone_number_id, waba_id),
            )

        log.info("WhatsApp credentials updated (phone_number_id: %s)", phone_number_id)
        return jsonify({"status": "saved", "service": "whatsapp"})

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

    return app