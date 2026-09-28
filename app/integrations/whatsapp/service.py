"""High-level WhatsApp service: connect, test, send, and persist outcomes."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import get_settings, mask
from app.database.db import get_connection, transaction
from app.integrations.whatsapp.base import DeliveryResult, DeliveryStatus
from app.integrations.whatsapp.credentials import (
    clear_whatsapp_credentials,
    load_whatsapp_credentials,
    store_whatsapp_credentials,
)
from app.integrations.whatsapp.factory import get_provider, provider_name
from app.logging import get_logger

log = get_logger("app.whatsapp.service")


@dataclass
class WhatsAppConnectionInfo:
    """Secret-safe description of the current WhatsApp connection."""

    provider: str
    configured: bool
    connected: bool
    phone_number_id: str | None
    waba_id: str | None
    token_present: bool
    token_hint: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "configured": self.configured,
            "connected": self.connected,
            "phone_number_id": self.phone_number_id,
            "waba_id": self.waba_id,
            "token_present": self.token_present,
            "token_hint": self.token_hint,
            "detail": self.detail,
        }


def connection_info() -> WhatsAppConnectionInfo:
    """Describe the WhatsApp connection without ever exposing the token."""
    provider = get_provider()
    creds = load_whatsapp_credentials() or {}
    token = creds.get("access_token", "")

    if provider.name == "stub":
        return WhatsAppConnectionInfo(
            provider="stub", configured=True, connected=False,
            phone_number_id=None, waba_id=None,
            token_present=False, token_hint="(stub - no token needed)",
            detail="Stub provider active. Nothing is sent to real WhatsApp numbers.",
        )

    row = get_connection().execute(
        "SELECT status FROM connections WHERE service = 'whatsapp';"
    ).fetchone()
    connected = bool(row and row["status"] == "CONNECTED")

    return WhatsAppConnectionInfo(
        provider=provider.name,
        configured=provider.is_configured(),
        connected=connected,
        phone_number_id=creds.get("phone_number_id"),
        waba_id=creds.get("waba_id"),
        token_present=bool(token),
        token_hint=mask(token) if token else "",
        detail="Meta Cloud credentials stored." if token else "No Meta credentials stored.",
    )


def connect_whatsapp(phone_number_id: str, waba_id: str, access_token: str,
                     activate: bool = True) -> dict[str, Any]:
    """Store credentials, run a live connection test, and persist the result.

    The connection is only marked CONNECTED when the test actually succeeds.
    """
    backend = store_whatsapp_credentials(phone_number_id, waba_id, access_token)
    log.info("WhatsApp credentials stored via %s (token %s)", backend, mask(access_token))

    # The stub provider cannot verify Meta credentials. Reporting CONNECTED
    # here would falsely imply the number can actually receive messages.
    provider = get_provider()
    if provider.name == "stub":
        result = DeliveryResult(
            status=DeliveryStatus.UNKNOWN, provider="stub",
            detail=(
                "Credentials saved, but WHATSAPP_PROVIDER=stub so they were not "
                "verified. Set WHATSAPP_PROVIDER=meta_cloud in .env and restart "
                "to test against the live Meta Cloud API."
            ),
        )
    else:
        result = test_whatsapp_connection()
    with transaction() as tx:
        status = "CONNECTED" if result.status is DeliveryStatus.SENT else "ERROR"
        tx.execute(
            """
            INSERT INTO connections
                (id, service, provider, status, phone_number_id, business_account_id,
                 last_tested_at, error_message, updated_at)
            VALUES ('conn-whatsapp', 'whatsapp', ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(service) DO UPDATE SET
                provider = excluded.provider, status = excluded.status,
                phone_number_id = excluded.phone_number_id,
                business_account_id = excluded.business_account_id,
                last_tested_at = CURRENT_TIMESTAMP,
                error_message = excluded.error_message,
                updated_at = CURRENT_TIMESTAMP;
            """,
            (
                provider_name(), status, phone_number_id, waba_id,
                None if status == "CONNECTED" else result.detail,
            ),
        )
        icon = "✓" if status == "CONNECTED" else "✕"
        tx.execute(
            "INSERT INTO events (event_type, message, icon, status) "
            "VALUES ('WHATSAPP_CONNECTION_TEST', ?, ?, ?);",
            (f"WhatsApp {status.lower()}: {result.detail}", icon,
             "SUCCESS" if status == "CONNECTED" else "WARNING"),
        )

    return {"storage": backend, "result": result}


def test_whatsapp_connection() -> DeliveryResult:
    """Run the active provider's connection test."""
    return get_provider().test_connection()


def disconnect_whatsapp() -> bool:
    """Remove stored credentials and mark the connection disconnected."""
    removed = clear_whatsapp_credentials()
    with transaction() as tx:
        tx.execute(
            "UPDATE connections SET status = 'DISCONNECTED', phone_number_id = NULL, "
            "business_account_id = NULL, account_identifier = NULL, "
            "error_message = NULL, updated_at = CURRENT_TIMESTAMP WHERE service = 'whatsapp';"
        )
        tx.execute(
            "INSERT INTO events (event_type, message, icon, status) "
            "VALUES ('WHATSAPP_DISCONNECTED', 'WhatsApp credentials removed', '✕', 'WARNING');"
        )
    return removed


def already_sent(lead_id: str) -> bool:
    """True when a confirmed WhatsApp message already exists for this lead."""
    row = get_connection().execute(
        "SELECT status FROM outreach WHERE lead_id = ? AND channel = 'whatsapp';",
        (lead_id,),
    ).fetchone()
    return bool(row and row["status"] == "SENT")


def send_whatsapp_message(
    *, lead_id: str, to: str, body: str, run_id: str | None = None,
    dry_run: bool | None = None,
) -> DeliveryResult:
    """Send one WhatsApp message with duplicate protection and persistence."""
    settings = get_settings()
    if dry_run is None:
        dry_run = settings.dry_run

    if already_sent(lead_id):
        log.warning("Duplicate blocked for lead %s - WhatsApp already SENT", lead_id)
        return DeliveryResult(
            status=DeliveryStatus.SENT, provider=get_provider().name, to=to,
            detail="SKIPPED_DUPLICATE: WhatsApp already sent for this lead.",
        )

    result = get_provider().send_text(to, body, dry_run=dry_run)

    with transaction() as tx:
        tx.execute(
            """
            INSERT INTO outreach
                (id, lead_id, channel, status, provider, provider_message_id,
                 message_body, error_message, run_id, sent_at)
            VALUES (?, ?, 'whatsapp', ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                f"out-{uuid.uuid4().hex[:12]}", lead_id, result.to_db_status(),
                result.provider, result.provider_message_id, body,
                None if result.confirmed else result.detail, run_id,
                datetime.now().isoformat(timespec="seconds") if result.confirmed else None,
            ),
        )
        tx.execute(
            "INSERT INTO events (event_type, lead_id, message, icon, status) "
            "VALUES ('WHATSAPP_ATTEMPT', ?, ?, ?, ?);",
            (
                lead_id, result.detail,
                "✓" if result.confirmed else ("○" if result.status is DeliveryStatus.UNKNOWN else "✕"),
                "SUCCESS" if result.confirmed else "WARNING",
            ),
        )
    return result