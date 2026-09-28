"""Gmail integration: OAuth authentication, message building, and sending."""

from app.integrations.gmail.oauth import (
    GmailAuthError,
    client_summary,
    exchange_code,
    get_service,
    is_configured,
    load_credentials,
    revoke_local_token,
    verify_connection,
)
from app.integrations.gmail.message import (
    MessageValidationError,
    build_email,
    validate_content,
    validate_recipient,
)
from app.integrations.gmail.sender import SendResult, already_sent, send_email

__all__ = [
    "GmailAuthError",
    "MessageValidationError",
    "SendResult",
    "already_sent",
    "build_email",
    "client_summary",
    "exchange_code",
    "get_service",
    "is_configured",
    "load_credentials",
    "revoke_local_token",
    "send_email",
    "validate_content",
    "validate_recipient",
    "verify_connection",
]