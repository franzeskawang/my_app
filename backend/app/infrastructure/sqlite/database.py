"""SQLite connection and idempotent database schema initialization."""
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from ...constants import (
    DEFAULT_CONVERSATION_ID,
    DEFAULT_OWNER_ID,
    DEFAULT_SOURCE_APP_ID,
)

DB_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).resolve().parents[3] / "data" / "expenses.db"))


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_column(db: sqlite3.Connection, table: str, definition: str) -> None:
    column_name = definition.split()[0]
    existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
    if column_name not in existing:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def initialize() -> None:
    """Create current tables and migrate the original global memory in place."""
    with closing(connect()) as db, db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                spent_on TEXT NOT NULL,
                category TEXT NOT NULL,
                comment TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_expenses_spent_on ON expenses(spent_on)")

        db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL DEFAULT 'local-user',
                created_by_app_id TEXT NOT NULL DEFAULT 'bookkeeping',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL DEFAULT 'bookkeeping-default',
                source_app_id TEXT NOT NULL DEFAULT 'bookkeeping',
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """)
        # Additive migration for databases created before conversations were scoped.
        _ensure_column(db, "conversation_messages", "conversation_id TEXT NOT NULL DEFAULT 'bookkeeping-default'")
        _ensure_column(db, "conversation_messages", "source_app_id TEXT NOT NULL DEFAULT 'bookkeeping'")
        db.execute("CREATE INDEX IF NOT EXISTS idx_conversation_messages_thread ON conversation_messages(conversation_id, id)")

        db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                conversation_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(conversation_id) REFERENCES conversations(id)
            )
        """)
        db.execute(
            "INSERT OR IGNORE INTO conversations(id, owner_id, created_by_app_id) VALUES (?, ?, ?)",
            (DEFAULT_CONVERSATION_ID, DEFAULT_OWNER_ID, DEFAULT_SOURCE_APP_ID),
        )

        # Preserve the previous single-summary table during migration; it remains harmless
        # for older developer databases and can be removed in a later schema cleanup.
        legacy_table = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'conversation_memory'"
        ).fetchone()
        if legacy_table:
            db.execute("""
                INSERT OR IGNORE INTO conversation_summaries(conversation_id, summary, updated_at)
                SELECT ?, summary, updated_at FROM conversation_memory WHERE id = 1
            """, (DEFAULT_CONVERSATION_ID,))
        db.execute("""
            INSERT OR IGNORE INTO conversation_summaries(conversation_id, summary)
            VALUES (?, '')
        """, (DEFAULT_CONVERSATION_ID,))
