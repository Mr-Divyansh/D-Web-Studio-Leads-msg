"""Shared test helpers: isolated temporary databases for safe test runs.

Tests MUST never write to the real ``data/outreach.db``. These helpers point the
application at a throwaway database for the duration of a test module.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

from app.config import get_settings
from app.database import db as db_module


class IsolatedDatabase:
    """Context manager redirecting the app to a temporary database directory."""

    def __init__(self, env_updates: dict[str, str] | None = None):
        self.env_updates = env_updates or {}
        self._temp_dir: str | None = None
        self._saved_env: dict[str, str | None] = {}

    def __enter__(self) -> Path:
        from app.database.db import init_database

        self._temp_dir = tempfile.mkdtemp(prefix="dws_test_")
        temp_path = Path(self._temp_dir)

        names = ["DB_PATH", "LEAD_IMPORT_PATH", "GMAIL_CREDENTIALS_PATH", "GMAIL_TOKEN_PATH", *self.env_updates]
        for name in names:
            self._saved_env[name] = os.environ.get(name)

        os.environ["DB_PATH"] = str(temp_path / "test_outreach.db")
        os.environ["LOG_LEVEL"] = "CRITICAL"

        # Drop cached settings and any open thread-local connection.
        get_settings(refresh=True)
        db_module._THREAD_LOCAL.__dict__.clear()

        init_database(get_settings().db_path)
        return temp_path

    def __exit__(self, exc_type, exc, tb) -> None:
        conn = getattr(db_module._THREAD_LOCAL, "connection", None)
        if conn is not None:
            conn.close()
        db_module._THREAD_LOCAL.__dict__.clear()

        for name, value in self._saved_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        get_settings(refresh=True)

        if self._temp_dir:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        self._temp_dir = None