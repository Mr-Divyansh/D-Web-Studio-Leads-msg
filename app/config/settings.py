"""Central configuration for the D Web Studio outreach system.

Single source of truth for runtime settings. Values are read from the local
``.env`` file and/or process environment. This module never stores secrets:
OAuth/API credentials live in ``credentials/`` or the OS keyring.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency present in requirements.txt
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

if load_dotenv is not None:
    load_dotenv(dotenv_path=ENV_FILE, override=False)

TRUTHY = {"1", "true", "yes", "on"}
FALSY = {"0", "false", "no", "off", ""}


class ConfigError(RuntimeError):
    """Raised when configuration is invalid or unsafe to run."""


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in TRUTHY:
        return True
    if value in FALSY:
        return False
    raise ConfigError(f"{name} must be a boolean (true/false), got {raw!r}")


def _int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    return value


def _float(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = float(str(raw).strip())
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    return value


def _text(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    return default if raw is None else str(raw).strip()


def _path(name: str, default: str) -> Path:
    raw = _text(name)
    candidate = Path(raw) if raw else Path(default)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def mask(value: str | None, keep: int = 4) -> str:
    """Return a display-safe version of a secret. Never returns the raw value."""
    if not value:
        return ""
    text = str(value)
    if len(text) <= keep:
        return "*" * len(text)
    return "*" * (len(text) - keep) + text[-keep:]


@dataclass(frozen=True)
class Settings:
    """Immutable, validated runtime configuration."""

    app_env: str
    dry_run: bool
    email_enabled: bool
    whatsapp_enabled: bool
    ai_enabled: bool
    max_retries: int
    email_delay_seconds: float
    whatsapp_delay_seconds: float
    priority_only: bool
    follow_up_enabled: bool
    campaign_max_messages: int
    campaign_messages_per_minute: int
    dashboard_host: str
    dashboard_port: int
    log_level: str
    db_path: Path
    lead_import_path: Path
    gmail_credentials_path: Path
    gmail_token_path: Path
    gmail_sender_name: str
    gmail_sender_email: str
    oauth_redirect_host: str
    whatsapp_provider: str
    ai_provider: str
    ai_model: str
    project_root: Path = field(default=PROJECT_ROOT)

    @property
    def is_live(self) -> bool:
        """True only when real messages may be sent."""
        return not self.dry_run

    @property
    def mode_label(self) -> str:
        return "LIVE" if self.is_live else "DRY RUN"

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def imports_dir(self) -> Path:
        return self.data_dir / "import"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "export"

    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"

    @property
    def credentials_dir(self) -> Path:
        return self.project_root / "credentials"

    def ensure_directories(self) -> None:
        """Create the local storage folders. Safe to call repeatedly."""
        for directory in (
            self.data_dir,
            self.imports_dir,
            self.exports_dir,
            self.logs_dir,
            self.credentials_dir,
            self.credentials_dir / "gmail",
            self.db_path.parent,
            self.gmail_token_path.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        """Fail fast on impossible combinations (called once at startup)."""
        if self.whatsapp_provider not in PROVIDER_CHOICES:
            raise ConfigError(
                f"WHATSAPP_PROVIDER must be one of {sorted(PROVIDER_CHOICES)}, "
                f"got {self.whatsapp_provider!r}"
            )
        if self.ai_provider not in AI_PROVIDER_CHOICES:
            raise ConfigError(
                f"AI_PROVIDER must be one of {sorted(AI_PROVIDER_CHOICES)}, "
                f"got {self.ai_provider!r}"
            )
        if self.dashboard_port < 1 or self.dashboard_port > 65535:
            raise ConfigError(f"DASHBOARD_PORT out of range: {self.dashboard_port}")

    def safety_warnings(self) -> list[str]:
        """Non-fatal configuration notices shown on the dashboard."""
        warnings: list[str] = []
        if self.is_live:
            warnings.append("LIVE mode: real messages will be sent.")
        if self.is_live and self.whatsapp_provider == "stub":
            warnings.append(
                "WHATSAPP_PROVIDER=stub while LIVE: WhatsApp delivery cannot "
                "be confirmed and will be recorded as UNKNOWN."
            )
        if self.is_live and not self.gmail_token_path.exists():
            warnings.append("Gmail is not authorized yet: connect it from the dashboard.")
        if self.ai_provider == "disabled":
            warnings.append("AI is disabled: approved fallback templates will be used.")
        return warnings

    def public_summary(self) -> dict[str, object]:
        """Dashboard/log safe snapshot. Contains no secrets by construction."""
        return {
            "app_env": self.app_env,
            "mode": self.mode_label,
            "dry_run": self.dry_run,
            "email_enabled": self.email_enabled,
            "whatsapp_enabled": self.whatsapp_enabled,
            "ai_enabled": self.ai_enabled,
            "ai_provider": self.ai_provider,
            "whatsapp_provider": self.whatsapp_provider,
            "priority_only": self.priority_only,
            "max_retries": self.max_retries,
            "database": str(self.db_path),
            "log_level": self.log_level,
        }


PROVIDER_CHOICES = {"stub", "meta_cloud"}
AI_PROVIDER_CHOICES = {"disabled", "openai", "anthropic", "local"}


def load_settings() -> Settings:
    """Build a Settings instance from the environment (no caching)."""
    settings = Settings(
        app_env=_text("APP_ENV", "local"),
        dry_run=_flag("DRY_RUN", True),
        email_enabled=_flag("EMAIL_ENABLED", True),
        whatsapp_enabled=_flag("WHATSAPP_ENABLED", True),
        ai_enabled=_flag("AI_ENABLED", True),
        max_retries=_int("MAX_RETRIES", 3, minimum=0),
        email_delay_seconds=_float("EMAIL_DELAY_SECONDS", 10.0, minimum=0.0),
        whatsapp_delay_seconds=_float("WHATSAPP_DELAY_SECONDS", 10.0, minimum=0.0),
        priority_only=_flag("PRIORITY_ONLY", True),
        follow_up_enabled=_flag("FOLLOW_UP_ENABLED", False),
        campaign_max_messages=_int("CAMPAIGN_MAX_MESSAGES", 200, minimum=1),
        campaign_messages_per_minute=_int("CAMPAIGN_MESSAGES_PER_MINUTE", 6, minimum=1),
        dashboard_host=_text("DASHBOARD_HOST", "127.0.0.1"),
        dashboard_port=_int("DASHBOARD_PORT", 8756, minimum=1),
        log_level=_text("LOG_LEVEL", "INFO").upper(),
        db_path=_path("DB_PATH", "data/outreach.db"),
        lead_import_path=_path("LEAD_IMPORT_PATH", "data/import/Lead for web dg.xlsx"),
        gmail_credentials_path=_path("GMAIL_CREDENTIALS_PATH", "credentials/gmail/credentials.json"),
        gmail_token_path=_path("GMAIL_TOKEN_PATH", "credentials/gmail/token.json"),
        gmail_sender_name=_text("GMAIL_SENDER_NAME", "D Web Studio"),
        gmail_sender_email=_text("GMAIL_SENDER_EMAIL"),
        oauth_redirect_host=_text("OAUTH_REDIRECT_HOST", ""),
        whatsapp_provider=_text("WHATSAPP_PROVIDER", "stub"),
        ai_provider=_text("AI_PROVIDER", "disabled"),
        ai_model=_text("AI_MODEL"),
    )
    settings.validate()
    return settings


_CACHED: Settings | None = None


def get_settings(refresh: bool = False) -> Settings:
    """Return the process-wide Settings singleton."""
    global _CACHED
    if _CACHED is None or refresh:
        _CACHED = load_settings()
        _CACHED.ensure_directories()
    return _CACHED