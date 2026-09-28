"""Factory that selects the active WhatsApp provider from configuration."""

from __future__ import annotations

from app.config import get_settings
from app.integrations.whatsapp.base import WhatsAppError, WhatsAppProvider
from app.integrations.whatsapp.meta_cloud import MetaCloudProvider
from app.integrations.whatsapp.stub import StubProvider
from app.logging import get_logger

log = get_logger("app.whatsapp.factory")

_PROVIDERS: dict[str, type[WhatsAppProvider]] = {
    "stub": StubProvider,
    "meta_cloud": MetaCloudProvider,
}


def build_provider(name: str) -> WhatsAppProvider:
    """Instantiate a provider by name."""
    key = (name or "").strip().lower()
    if key not in _PROVIDERS:
        raise WhatsAppError(
            f"Unknown WhatsApp provider {name!r}. Valid options: {sorted(_PROVIDERS)}"
        )
    return _PROVIDERS[key]()


def get_provider() -> WhatsAppProvider:
    """Return the provider selected by WHATSAPP_PROVIDER in the environment."""
    return build_provider(get_settings().whatsapp_provider)


def provider_name() -> str:
    return get_settings().whatsapp_provider