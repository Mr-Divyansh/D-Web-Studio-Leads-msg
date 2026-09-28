"""Application logging with mandatory secret redaction.

Every log record passes through :class:`RedactingFormatter` so credentials,
OAuth tokens and API keys can never reach the console, log files, or the
activity history. This is a hard requirement of the project rules.
"""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILENAME = "outreach.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

REDACTED = "***REDACTED***"

SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)(\"?(?:client_secret|access_token|refresh_token|api_key|apikey|password|auth_token|id_token|verify_token)\"?\s*[:=]\s*\"?)([^\s\",}]+)"), r"\1" + REDACTED),
    (re.compile(r"GOCSPX-[A-Za-z0-9_\-]+"), "GOCSPX-" + REDACTED),
    (re.compile(r"ya29\.[A-Za-z0-9_\-\.]+"), "ya29." + REDACTED),
    (re.compile(r"EAAG[A-Za-z0-9_\-]+"), "EAAG" + REDACTED),
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "sk-" + REDACTED),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.=]{10,}"), "Bearer " + REDACTED),
)


def redact(text: str) -> str:
    """Remove anything that looks like a credential from a string."""
    if not text:
        return text
    cleaned = str(text)
    for pattern, replacement in SECRET_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


class RedactingFormatter(logging.Formatter):
    """Formatter that scrubs credentials from the final formatted message."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        return redact(super().format(record))


class SecretScrubbingFilter(logging.Filter):
    """Scrub record payloads so third-party handlers stay safe too."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: (redact(str(v)) if isinstance(v, str) else v) for k, v in record.args.items()}
            else:
                record.args = tuple(redact(str(a)) if isinstance(a, str) else a for a in record.args)
        return True


_CONFIGURED = False


def configure_logging(level: str = "INFO", log_dir: Path | None = None) -> logging.Logger:
    """Configure root logging once (console + rotating file)."""
    global _CONFIGURED

    if log_dir is None:
        from app.config import get_settings

        log_dir = get_settings().logs_dir
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    numeric_level = getattr(logging, str(level).upper(), logging.INFO)
    root.setLevel(numeric_level)

    if _CONFIGURED:
        return logging.getLogger("app")

    formatter = RedactingFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    scrubber = SecretScrubbingFilter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(scrubber)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        Path(log_dir) / LOG_FILENAME, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(scrubber)
    root.addHandler(file_handler)

    _CONFIGURED = True
    return logging.getLogger("app")


def get_logger(name: str = "app") -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)