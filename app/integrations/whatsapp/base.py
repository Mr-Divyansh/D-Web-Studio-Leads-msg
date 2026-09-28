"""Abstract WhatsApp provider interface.

Every provider must return a ``DeliveryResult``. The single most important rule
in this module: when delivery cannot be confirmed, the status MUST be
``UNKNOWN``. Guessing "sent" is a violation of the system contract.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeliveryStatus(str, Enum):
    """Terminal state of one WhatsApp delivery attempt."""

    SENT = "SENT"                 # provider confirmed acceptance
    FAILED = "FAILED"             # provider rejected the request
    UNKNOWN = "UNKNOWN"           # outcome could not be determined
    NOT_AVAILABLE = "NOT_AVAILABLE"  # lead has no usable phone number
    DRY_RUN = "DRY_RUN"           # validated only, nothing transmitted


class WhatsAppError(RuntimeError):
    """Raised for provider configuration or transport problems."""


@dataclass
class DeliveryResult:
    """Outcome of a single WhatsApp send attempt."""

    status: DeliveryStatus
    provider: str
    to: str | None = None
    provider_message_id: str | None = None
    detail: str = ""
    raw_response: dict[str, Any] | None = field(default=None, repr=False)

    @property
    def confirmed(self) -> bool:
        """True only when the provider explicitly confirmed the message."""
        return self.status is DeliveryStatus.SENT

    def to_db_status(self) -> str:
        return self.status.value


class WhatsAppProvider(abc.ABC):
    """Base class for all WhatsApp delivery providers."""

    name: str = "base"

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """True when the provider has everything it needs to send."""

    @abc.abstractmethod
    def send_text(self, to: str, body: str, *, dry_run: bool = False) -> DeliveryResult:
        """Send a plain-text message to a normalized 10-digit number."""

    def send_template(self, to: str, template_name: str, parameters: list[str],
                      *, dry_run: bool = False) -> DeliveryResult:
        """Send a pre-approved template. Optional for providers without templates."""
        raise WhatsAppError(f"{self.name} does not support template messages.")

    def test_connection(self) -> DeliveryResult:
        """Verify credentials without sending anything to a real lead."""
        return DeliveryResult(
            status=DeliveryStatus.UNKNOWN if self.is_configured() else DeliveryStatus.FAILED,
            provider=self.name,
            detail="Provider configured." if self.is_configured() else "Provider not configured.",
        )

    @staticmethod
    def normalize_phone(raw: str | None) -> str | None:
        """Normalize to 10 digits (India) or E.164 when an explicit country code exists."""
        if not raw:
            return None
        digits = "".join(ch for ch in str(raw) if ch.isdigit())
        if not digits:
            return None
        if len(digits) > 10 and digits.startswith("91"):
            return digits[-10:]
        if len(digits) >= 10:
            return digits[-10:]
        return None