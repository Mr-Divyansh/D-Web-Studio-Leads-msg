"""Configuration package: loads and validates local settings."""

from app.config.settings import PROJECT_ROOT, ConfigError, Settings, get_settings

__all__ = ["PROJECT_ROOT", "ConfigError", "Settings", "get_settings"]