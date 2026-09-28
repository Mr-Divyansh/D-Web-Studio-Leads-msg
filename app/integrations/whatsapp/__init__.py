"""WhatsApp integration: provider abstraction, credentials, and service layer."""

from app.integrations.whatsapp.base import (
    DeliveryResult,
    DeliveryStatus,
    WhatsAppError,
    WhatsAppProvider,
)
from app.integrations.whatsapp.credentials import (
    clear_whatsapp_credentials,
    load_whatsapp_credentials,
    store_whatsapp_credentials,
)
from app.integrations.whatsapp.factory import build_provider, get_provider, provider_name
from app.integrations.whatsapp.service import (
    WhatsAppConnectionInfo,
    connect_whatsapp,
    connection_info,
    disconnect_whatsapp,
    send_whatsapp_message,
    test_whatsapp_connection,
)

__all__ = [
    "DeliveryResult",
    "DeliveryStatus",
    "WhatsAppConnectionInfo",
    "WhatsAppError",
    "WhatsAppProvider",
    "build_provider",
    "clear_whatsapp_credentials",
    "connect_whatsapp",
    "connection_info",
    "disconnect_whatsapp",
    "get_provider",
    "load_whatsapp_credentials",
    "provider_name",
    "send_whatsapp_message",
    "store_whatsapp_credentials",
    "test_whatsapp_connection",
]