"""Offline stub provider: simulates delivery without any network access.

This is the DEFAULT provider. It exists so the whole pipeline can be exercised
safely before real Meta credentials are configured. It never contacts WhatsApp.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.integrations.whatsapp.base import (
    DeliveryResult,
    DeliveryStatus,
    WhatsAppProvider,
)
from app.logging import get_logger

log = get_logger("app.whatsapp.stub")


class StubProvider(WhatsAppProvider):
    """Simulates WhatsApp delivery locally. Safe for dry runs and testing."""

    name = "stub"

    def is_configured(self) -> bool:
        return True

    def send_text(self, to: str, body: str, *, dry_run: bool = False) -> DeliveryResult:
        phone = self.normalize_phone(to)
        if not phone:
            return DeliveryResult(
                status=DeliveryStatus.NOT_AVAILABLE,
                provider=self.name,
                to=to,
                detail="No usable phone number.",
            )

        if dry_run:
            log.info("[STUB][DRY RUN] would send %d chars to %s", len(body), phone)
            return DeliveryResult(
                status=DeliveryStatus.DRY_RUN,
                provider=self.name,
                to=phone,
                detail="Simulated only - nothing transmitted.",
            )

        # Deterministic pseudo message ID so tests are reproducible.
        digest = hashlib.sha256(f"{phone}:{body}".encode("utf-8")).hexdigest()[:16]
        message_id = f"stub-{digest}"
        log.info("[STUB] simulated delivery to %s (%s)", phone, message_id)
        return DeliveryResult(
            status=DeliveryStatus.SENT,
            provider=self.name,
            to=phone,
            provider_message_id=message_id,
            detail="Simulated delivery (stub provider).",
            raw_response={"simulated": True, "message_id": message_id},
        )

    def test_connection(self) -> DeliveryResult:
        return DeliveryResult(
            status=DeliveryStatus.SENT,
            provider=self.name,
            detail="Stub provider active. No real messages can be sent.",
        )