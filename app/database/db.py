"""SQLite database engine, connection factory, and schema migrations."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterator

from app.config import get_settings
from app.logging import get_logger

log = get_logger("app.database")

_THREAD_LOCAL = threading.local()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a thread-local SQLite connection with WAL mode and row factories enabled."""
    if db_path is None:
        db_path = get_settings().db_path

    conn = getattr(_THREAD_LOCAL, "connection", None)
    current_path = getattr(_THREAD_LOCAL, "db_path", None)

    if conn is None or current_path != db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False,
            timeout=30.0,
            isolation_level=None,  # autocommit mode; manage transactions explicitly
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        _THREAD_LOCAL.connection = conn
        _THREAD_LOCAL.db_path = db_path

    return conn


@contextmanager
def transaction(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Execute a block within an explicit SQLite transaction."""
    conn = get_connection(db_path)
    conn.execute("BEGIN IMMEDIATE;")
    try:
        yield conn
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def init_database(db_path: Path | None = None) -> None:
    """Apply the foundational schema and default seeds."""
    if db_path is None:
        db_path = get_settings().db_path

    schema_file = Path(__file__).parent / "schema.sql"
    schema_sql = schema_file.read_text(encoding="utf-8")

    conn = get_connection(db_path)
    conn.executescript(schema_sql)

    # Initialize default connection records if they do not exist
    default_connections = [
        ("conn-gmail", "gmail", "gmail_oauth", "DISCONNECTED"),
        ("conn-whatsapp", "whatsapp", "stub", "DISCONNECTED"),
        ("conn-ai", "ai", "disabled", "CONNECTED"),
    ]
    for cid, service, provider, status in default_connections:
        conn.execute(
            """
            INSERT OR IGNORE INTO connections (id, service, provider, status)
            VALUES (?, ?, ?, ?);
            """,
            (cid, service, provider, status),
        )

    # Record baseline schema migration
    conn.execute(
        "INSERT OR IGNORE INTO schema_migrations (version) VALUES ('1.0.0');"
    )
    log.info("Database initialized successfully at %s", db_path)


def reset_database(db_path: Path | None = None) -> None:
    """Completely wipe and re-initialize the database (used in testing)."""
    if db_path is None:
        db_path = get_settings().db_path
    conn = getattr(_THREAD_LOCAL, "connection", None)
    if conn:
        conn.close()
        _THREAD_LOCAL.connection = None
    if db_path.exists():
        db_path.unlink()
    init_database(db_path)