"""Gmail send operations with duplicate-send prevention."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import get_settings
from app.database.db import transaction
from app.integrations.gmail.message import BuiltMessage, MessageValidationError, build_email
from app.integrations.gmail.oauth import GmailAuthError, get_service
from app.logging import get_logger

log = get_logger("app.gmail.sender")


@dataclass
class SendResult:
    status: str            # SENT | FAILED | SKIPPED_DUPLICATE | DRY_RUN
    provider: str          # gmail
    message_id: str | None
    detail: str
    subject: str | None = None
    body: str | None = None


def already_sent(lead_id: str, channel: str = "email") -> bool:
    """True when this lead/channel already has a SENT outreach record.

    This is the last line of defence against duplicate sending. The database
    also enforces UNIQUE(lead_id, channel).
    """
    from app.database.db import get_connection

    row = get_connection().execute(
        "SELECT status FROM outreach WHERE lead_id = ? AND channel = ?;",
        (lead_id, channel),
    ).fetchone()
    return bool(row and row["status"] == "SENT")


def _record(
    lead_id: str,
    result: SendResult,
    run_id: str | None = None,
    template_version: str = "v1",
) -> None:
    """Persist the delivery attempt."""
    with transaction() as conn:
        conn.execute(
            """
            INSERT INTO outreach (
                id, lead_id, channel, status, provider, provider_message_id,
                template_version, subject, message_body, error_message, run_id, sent_at
            ) VALUES (?, ?, 'email', ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                f"out-{uuid.uuid4().hex[:12]}",
                lead_id,
                result.status,
                result.provider,
                result.message_id,
                template_version,
                result.subject,
                result.body,
                None if result.status in {"SENT", "DRY_RUN"} else result.detail,
                run_id,
                datetime.now().isoformat(timespec="seconds")
                if result.status == "SENT" else None,
            ),
        )


def send_email(
    *,
    lead_id: str,
    to: str,
    subject: str,
    body: str,
    run_id: str | None = None,
    dry_run: bool | None = None,
) -> SendResult:
    """Send (or simulate) one email for one lead.

    Order of operations is deliberate:
      1. duplicate check   2. build + validate   3. send   4. record
    Nothing is transmitted before the message passes validation, and DRY_RUN
    never touches the network.
    """
    settings = get_settings()
    if dry_run is None:
        dry_run = settings.dry_run

    if already_sent(lead_id):
        log.warning("Duplicate blocked for lead %s - email already SENT", lead_id)
        return SendResult("SKIPPED_DUPLICATE", "gmail", None, "Email already sent for this lead.")

    try:
        built: BuiltMessage = build_email(
            to=to,
            subject=subject,
            body=body,
            sender_name=settings.gmail_sender_name,
            sender_email=settings.gmail_sender_email or None,
        )
    except MessageValidationError as exc:
        result = SendResult("FAILED", "gmail", None, str(exc), subject, body)
        _record(lead_id, result, run_id)
        return result

    if dry_run:
        result = SendResult("DRY_RUN", "gmail", None,
                            "Validated only - nothing sent (DRY RUN).", built.subject, built.body)
        _record(lead_id, result, run_id)
        log.info("DRY RUN: email to %s validated, not sent.", built.to)
        return result

    try:
        service = get_service()
        sent = service.users().messages().send(
            userId="me", body={"raw": built.raw}
        ).execute()
        message_id = sent.get("id")
        result = SendResult("SENT", "gmail", message_id, "Email sent.", built.subject, built.body)
        _record(lead_id, result, run_id)
        log.info("Email sent to %s (message id %s)", built.to, message_id)
        return result
    except GmailAuthError as exc:
        result = SendResult("FAILED", "gmail", None, str(exc), built.subject, built.body)
        _record(lead_id, result, run_id)
        return result
    except Exception as exc:  # noqa: BLE001
        log.error("Gmail send failed: %s", exc)
        result = SendResult("FAILED", "gmail", None, f"Gmail API error: {exc}", built.subject, built.body)
        _record(lead_id, result, run_id)
        return result