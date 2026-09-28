"""RFC 2822 email message construction with strict safety validation."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from app.logging import get_logger

log = get_logger("app.gmail.message")

RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

# Phrases that indicate the AI invented a personal fact.
BANNED_CLAIMS = (
    "as i mentioned",
    "as discussed earlier",
    "like we spoke",
    "you told me",
    "your website",
    "your business",
    "your company",
    "i know your",
    "we have worked together",
    "your recent",
    "your portfolio",
)


class MessageValidationError(ValueError):
    """Raised when a message fails a pre-send safety gate."""


@dataclass
class BuiltMessage:
    raw: str            # base64url encoded RFC 2822 message, ready for the API
    subject: str
    body: str
    to: str


def validate_recipient(address: str) -> str:
    """Validate and normalize an email address."""
    cleaned = (address or "").strip().lower()
    if not cleaned:
        raise MessageValidationError("Recipient email is empty.")
    if not RE_EMAIL.match(cleaned):
        raise MessageValidationError(f"Invalid email address: {address!r}")
    return cleaned


def validate_content(subject: str, body: str) -> None:
    """Pre-send safety gates: never send empty or fabricated content."""
    if not subject or not subject.strip():
        raise MessageValidationError("Subject line is empty.")
    if not body or not body.strip():
        raise MessageValidationError("Message body is empty.")
    if len(body.strip()) < 40:
        raise MessageValidationError("Message body is too short to be meaningful.")
    if len(body) > 20000:
        raise MessageValidationError("Message body exceeds 20,000 characters.")

    lowered = body.lower()
    for phrase in BANNED_CLAIMS:
        if phrase in lowered:
            raise MessageValidationError(
                f"Blocked: message asserts an unverified personal fact ({phrase!r})."
            )
    # Unresolved placeholders mean the template was not filled correctly.
    if re.search(r"\{\{.*?\}\}|<[A-Z_]{3,}>|\bTODO\b|\[INSERT", body):
        raise MessageValidationError("Message contains unfilled placeholders.")


def build_email(
    *,
    to: str,
    subject: str,
    body: str,
    sender_name: str,
    sender_email: str | None = None,
) -> BuiltMessage:
    """Build a plain-text email and return the base64url payload for Gmail."""
    recipient = validate_recipient(to)
    validate_content(subject, body)

    message = EmailMessage()
    if sender_email:
        message["From"] = formataddr((sender_name, sender_email))
    else:
        # No explicit address configured: the authorized Gmail account supplies
        # the envelope sender. formataddr() requires a 2-tuple, so use the name.
        message["From"] = sender_name
    message["To"] = recipient
    message["Subject"] = subject.strip()
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain="dwebstudio.local")
    message.set_content(body.strip(), subtype="plain", charset="utf-8")

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    log.info("Built email for %s (subject=%r)", recipient, subject[:40])
    return BuiltMessage(raw=raw, subject=subject.strip(), body=body.strip(), to=recipient)