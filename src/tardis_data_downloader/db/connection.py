"""
SQLite database connection management for Tardis Data Downloader.

Provides thread-safe connections with WAL mode for concurrent access.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from loguru import logger

SCHEMA_VERSION = "1"

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange TEXT NOT NULL,
    data_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(exchange, data_type, symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_files_lookup
    ON files(exchange, data_type, symbol, date);
CREATE INDEX IF NOT EXISTS idx_files_exchange_datatype
    ON files(exchange, data_type);

CREATE TABLE IF NOT EXISTS download_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile TEXT NOT NULL,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    data_type TEXT NOT NULL,
    last_date TEXT NOT NULL,
    files_count INTEGER NOT NULL DEFAULT 0,
    last_updated TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(profile, exchange, symbol, data_type)
);

CREATE INDEX IF NOT EXISTS idx_state_profile
    ON download_state(profile);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class TardisDB:
    """
    Thread-safe SQLite database for tracking downloaded files and state.

    Uses WAL mode for concurrent read/write access and thread-local
    connections for safe multi-threaded usage.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._lock = threading.Lock()

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

        # Lazy-init repositories
        from tardis_data_downloader.db.repository import FileRepository, StateRepository

        self.file_repo = FileRepository(self)
        self.state_repo = StateRepository(self)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        conn = getattr(self._local, "connection", None)
        if conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=10.0,
                isolation_level=None,  # autocommit; we manage transactions explicitly
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._local.connection = conn
        return conn

    @property
    def conn(self) -> sqlite3.Connection:
        """Current thread's database connection."""
        return self._get_connection()

    def _init_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        conn = self._get_connection()
        conn.executescript(SCHEMA_SQL)

        # Set schema version if not present
        existing = conn.execute(
            "SELECT value FROM metadata WHERE key = 'schema_version'"
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO metadata (key, value) VALUES ('schema_version', ?)",
                (SCHEMA_VERSION,),
            )
            conn.commit()

        logger.debug(f"Database initialized at {self.db_path}")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL statement."""
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, params_seq) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        return self.conn.executemany(sql, params_seq)

    def commit(self) -> None:
        """Commit the current transaction."""
        self.conn.commit()

    def begin(self) -> None:
        """Begin an explicit transaction."""
        self.conn.execute("BEGIN")

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self.conn.rollback()

    def close(self) -> None:
        """Close the thread-local connection if open."""
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            conn.close()
            self._local.connection = None

    def __enter__(self) -> "TardisDB":
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    def get_metadata(self, key: str) -> str | None:
        """Get a metadata value."""
        row = self.execute(
            "SELECT value FROM metadata WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata value."""
        self.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.commit()
