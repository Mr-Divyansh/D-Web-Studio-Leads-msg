"""Official WhatsApp Business Cloud API provider (Meta).

Uses the Graph API to send text and template messages. Credentials are read
from the OS keyring and are never written to SQLite, .env, or the repository.
"""

from __future__ import annotations

from typing import Any

import requests

from app.integrations.whatsapp.base import (
    DeliveryResult,
    DeliveryStatus,
    WhatsAppError,
    WhatsAppProvider,
)
from app.integrations.whatsapp.credentials import load_whatsapp_credentials
from app.logging import get_logger

log = get_logger("app.whatsapp.meta")

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


class MetaCloudProvider(WhatsAppProvider):
    """Sends messages through the official Meta WhatsApp Business Cloud API."""

    name = "meta_cloud"

    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def _creds(self) -> dict[str, Any] | None:
        return load_whatsapp_credentials()

    def is_configured(self) -> bool:
        creds = self._creds()
        return bool(creds and creds.get("phone_number_id") and creds.get("access_token"))

    def _headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def send_text(self, to: str, body: str, *, dry_run: bool = False) -> DeliveryResult:
        phone = self.normalize_phone(to)
        if not phone:
            return DeliveryResult(
                status=DeliveryStatus.NOT_AVAILABLE,
                provider=self.name, to=to, detail="No usable phone number.",
            )

        creds = self._creds()
        if not creds:
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name, to=phone,
                detail="WhatsApp credentials not configured.",
            )

        if dry_run:
            log.info("[META][DRY RUN] would send %d chars to %s", len(body), phone)
            return DeliveryResult(
                status=DeliveryStatus.DRY_RUN, provider=self.name, to=phone,
                detail="Validated only - nothing transmitted (DRY RUN).",
            )

        url = f"{GRAPH_BASE}/{creds['phone_number_id']}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        try:
            response = requests.post(
                url, headers=self._headers(creds["access_token"]),
                json=payload, timeout=self.timeout,
            )
            data = response.json()
        except requests.RequestException as exc:
            log.error("Meta transport error: %s", exc)
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name, to=phone,
                detail=f"Network error: {exc}",
            )

        return self._interpret(response.status_code, data, phone)

    def send_template(self, to: str, template_name: str, parameters: list[str],
                      *, dry_run: bool = False) -> DeliveryResult:
        phone = self.normalize_phone(to)
        if not phone:
            return DeliveryResult(
                status=DeliveryStatus.NOT_AVAILABLE, provider=self.name, to=to,
                detail="No usable phone number.",
            )
        creds = self._creds()
        if not creds:
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name, to=phone,
                detail="WhatsApp credentials not configured.",
            )
        if dry_run:
            return DeliveryResult(
                status=DeliveryStatus.DRY_RUN, provider=self.name, to=phone,
                detail=f"Template {template_name!r} validated only.",
            )

        url = f"{GRAPH_BASE}/{creds['phone_number_id']}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in parameters],
                }],
            },
        }
        try:
            response = requests.post(
                url, headers=self._headers(creds["access_token"]),
                json=payload, timeout=self.timeout,
            )
            data = response.json()
        except requests.RequestException as exc:
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name, to=phone,
                detail=f"Network error: {exc}",
            )
        return self._interpret(response.status_code, data, phone)

    def _interpret(self, status_code: int, data: dict[str, Any], phone: str) -> DeliveryResult:
        """Map a Graph API response to a DeliveryResult.

        A 2xx without a message id is reported as UNKNOWN, never as SENT.
        """
        if 200 <= status_code < 300:
            message_id = (
                data.get("messages", [{}])[0].get("id")
                if data.get("messages") else None
            )
            if message_id:
                log.info("Meta confirmed delivery to %s (%s)", phone, message_id)
                return DeliveryResult(
                    status=DeliveryStatus.SENT, provider=self.name, to=phone,
                    provider_message_id=message_id, detail="Accepted by WhatsApp Cloud API.",
                    raw_response=data,
                )
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name, to=phone,
                detail="API returned success but no message id; delivery unconfirmed.",
                raw_response=data,
            )

        error = data.get("error", {})
        code = error.get("code")
        subcode = error.get("error_subcode")
        message = error.get("message", "Unknown Meta API error")

        # 131047 = re-engagement window, 131026 = message undeliverable.
        # Both mean the number cannot be reached right now -> UNKNOWN, not SENT.
        if code in (131047, 131026, 131052) or subcode == 2494010:
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name, to=phone,
                detail=f"Number not currently reachable ({code}). {message}",
                raw_response=data,
            )

        return DeliveryResult(
            status=DeliveryStatus.FAILED, provider=self.name, to=phone,
            detail=f"HTTP {status_code} code={code}: {message}",
            raw_response=data,
        )

    def test_connection(self) -> DeliveryResult:
        """Validate the token and phone number ID without messaging a lead."""
        creds = self._creds()
        if not creds:
            return DeliveryResult(
                status=DeliveryStatus.FAILED, provider=self.name,
                detail="No WhatsApp credentials stored.",
            )
        url = f"{GRAPH_BASE}/{creds['phone_number_id']}"
        params = {"fields": "display_name,verified_name,quality_rating", "access_token": creds["access_token"]}
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            data = response.json()
        except requests.RequestException as exc:
            return DeliveryResult(
                status=DeliveryStatus.UNKNOWN, provider=self.name,
                detail=f"Network error: {exc}",
            )

        if response.status_code == 200 and "id" in data:
            return DeliveryResult(
                status=DeliveryStatus.SENT, provider=self.name,
                provider_message_id=data.get("id"),
                detail=(
                    f"Connected. Display name: {data.get('verified_name') or data.get('display_name') or 'n/a'}"
                    f" | Quality: {data.get('quality_rating', 'UNKNOWN')}"
                ),
                raw_response=data,
            )

        error = data.get("error", {})
        return DeliveryResult(
            status=DeliveryStatus.FAILED, provider=self.name,
            detail=f"HTTP {response.status_code} code={error.get('code')}: {error.get('message')}",
            raw_response=data,
        )