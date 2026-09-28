"""Gmail OAuth 2.0 authentication (installed-app / loopback flow).

Handles: authorization URL generation, code exchange, token persistence,
automatic refresh, and connection verification. Tokens are stored locally in
``credentials/gmail/token.json`` and are never logged in full.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import get_settings, mask
from app.logging import get_logger

log = get_logger("app.gmail.oauth")

# Minimum scopes needed to send mail and later detect replies.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailAuthError(RuntimeError):
    """Raised when Gmail authentication or API access fails."""


@dataclass
class ConnectionStatus:
    authorized: bool
    account_email: str | None
    scopes: list[str]
    expired: bool
    detail: str


def _credentials_path() -> Path:
    return get_settings().gmail_credentials_path


def _token_path() -> Path:
    return get_settings().gmail_token_path


def client_config() -> dict[str, Any]:
    """Load the installed-app OAuth client configuration."""
    path = _credentials_path()
    if not path.exists():
        raise GmailAuthError(
            f"Missing {path.name}. Place your Google OAuth client JSON at {path}."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GmailAuthError(f"{path.name} is not valid JSON: {exc}") from exc

    if "installed" not in data:
        raise GmailAuthError(
            "Expected an INSTALLED app client (JSON key \"installed\"). "
            "In Google Cloud Console the OAuth client type must be 'Desktop app'."
        )
    return data


def is_configured() -> bool:
    """True when a usable OAuth client file is present."""
    try:
        client_config()
        return True
    except GmailAuthError:
        return False


def client_summary() -> dict[str, Any]:
    """Secret-safe description of the configured client."""
    try:
        cfg = client_config()["installed"]
    except GmailAuthError as exc:
        return {"configured": False, "error": str(exc)}
    return {
        "configured": True,
        "client_id": cfg.get("client_id", ""),
        "project_id": cfg.get("project_id", ""),
        "client_secret": mask(cfg.get("client_secret", "")),
        "redirect_uris": cfg.get("redirect_uris", []),
    }


def build_authorization_url(state: str, redirect_uri: str) -> str:
    """Create the Google consent URL the operator must open in a browser."""
    cfg = client_config()["installed"]
    flow = InstalledAppFlow.from_client_config(
        {"installed": cfg}, scopes=SCOPES, redirect_uri=redirect_uri
    )
    url, _ = flow.authorization_url(
        access_type="offline",          # request a refresh token
        include_granted_scopes="true",
        prompt="consent",               # always show the consent screen
        state=state,
    )
    log.info("Authorization URL generated for state=%s", state[:8])
    return url


def exchange_code(code: str, redirect_uri: str) -> Credentials:
    """Exchange the ?code= callback value for a token and persist it."""
    cfg = client_config()["installed"]
    flow = InstalledAppFlow.from_client_config(
        {"installed": cfg}, scopes=SCOPES, redirect_uri=redirect_uri
    )
    flow.fetch_token(code=code)

    creds: Credentials = flow.credentials
    _token_path().parent.mkdir(parents=True, exist_ok=True)
    _token_path().write_text(creds.to_json(), encoding="utf-8")
    log.info("Token stored. refresh_token present: %s", bool(creds.refresh_token))
    return creds


def load_credentials() -> Credentials | None:
    """Load stored credentials, refreshing them automatically when expired."""
    path = _token_path()
    if not path.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    except (ValueError, json.JSONDecodeError) as exc:
        log.error("Stored token is unreadable: %s", exc)
        return None

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            path.write_text(creds.to_json(), encoding="utf-8")
            log.info("Access token refreshed automatically.")
        except Exception as exc:  # noqa: BLE001 - surfaced to the operator
            log.error("Token refresh failed: %s", exc)
            return None
    return creds


def get_service():
    """Return an authenticated Gmail API service client."""
    creds = load_credentials()
    if creds is None:
        raise GmailAuthError("Gmail is not authorized. Connect it from the dashboard first.")
    from googleapiclient.discovery import build

    try:
        return build("gmail", "v1", credentials=creds, cache_discovery=False)
    except Exception as exc:  # noqa: BLE001
        raise GmailAuthError(f"Could not build Gmail service: {exc}") from exc


def verify_connection() -> ConnectionStatus:
    """Test the connection and read the authorized account address."""
    creds = load_credentials()
    if creds is None:
        return ConnectionStatus(False, None, [], True, "Not authorized")

    scopes = list(getattr(creds, "scopes", []) or [])
    try:
        service = get_service()
        profile = service.users().getProfile(userId="me").execute()
        email_addr = profile.get("emailAddress")
        total = profile.get("messagesTotal", "?")
        log.info("Gmail connection verified for %s", email_addr)
        return ConnectionStatus(True, email_addr, scopes, bool(creds.expired),
                                f"Connected. {total} messages in mailbox.")
    except GmailAuthError as exc:
        return ConnectionStatus(False, None, scopes, True, str(exc))
    except Exception as exc:  # noqa: BLE001
        log.error("Gmail connection test failed: %s", exc)
        return ConnectionStatus(False, None, scopes, True, f"API error: {exc}")


def revoke_local_token() -> bool:
    """Delete the local token so the operator must re-authorize."""
    path = _token_path()
    if path.exists():
        path.unlink()
        log.info("Local Gmail token removed.")
        return True
    return False