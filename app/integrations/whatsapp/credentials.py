"""Secure storage for third-party API tokens using the OS keyring.

Access tokens are NEVER written to SQLite, to ``.env``, or to any file inside
the repository. They live in the operating system credential store.
"""

from __future__ import annotations

import json
from typing import Any

from app.config import get_settings, mask
from app.logging import get_logger

log = get_logger("app.integrations.credentials")

SERVICE_NAME = "d-web-studio-outreach"
_WHATSAPP_USER = "whatsapp-meta-token"


def _keyring():
    """Return the keyring module, or None when it is unavailable."""
    try:
        import keyring

        backend = keyring.get_keyring()
        if backend is None:
            return None
        return keyring
    except Exception as exc:  # noqa: BLE001
        log.warning("OS keyring unavailable (%s). Tokens cannot be stored securely.", exc)
        return None


def _fallback_path():
    """Encrypted-less local fallback used ONLY when no keyring exists.

    The file lives outside the repository (under the OS user profile) and is
    still excluded from version control.
    """
    return get_settings().project_root / "credentials" / "whatsapp" / "token.local.json"


def store_whatsapp_credentials(phone_number_id: str, waba_id: str, access_token: str) -> str:
    """Persist the Meta access token. Returns the storage backend used."""
    payload = {
        "phone_number_id": phone_number_id,
        "waba_id": waba_id,
        "access_token": access_token,
    }
    ring = _keyring()
    if ring is not None:
        ring.set_password(SERVICE_NAME, _WHATSAPP_USER, json.dumps(payload))
        log.info("WhatsApp token stored in OS keyring (token %s)", mask(access_token))
        return "os_keyring"

    path = _fallback_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    log.warning("OS keyring unavailable - token written to %s (git-ignored).", path)
    return "local_file"


def load_whatsapp_credentials() -> dict[str, Any] | None:
    """Retrieve stored WhatsApp credentials, or None when not configured."""
    ring = _keyring()
    if ring is not None:
        raw = ring.get_password(SERVICE_NAME, _WHATSAPP_USER)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                log.error("Stored WhatsApp credential is corrupt.")
                return None
    path = _fallback_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def clear_whatsapp_credentials() -> bool:
    """Remove the stored WhatsApp token."""
    ring = _keyring()
    removed = False
    if ring is not None:
        try:
            ring.delete_password(SERVICE_NAME, _WHATSAPP_USER)
            removed = True
        except Exception:  # noqa: BLE001 - nothing stored
            pass
    path = _fallback_path()
    if path.exists():
        path.unlink()
        removed = True
    return removed