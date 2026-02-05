from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    product TEXT NOT NULL,
    installed_version TEXT,
    latest_version TEXT,
    update_available INTEGER,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def insert_check(conn: sqlite3.Connection, payload: dict[str, Any]) -> int:
    cursor = conn.execute(
        """
        INSERT INTO checks (
            created_at, product, installed_version, latest_version,
            update_available, source_url, status, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["created_at"],
            payload["product"],
            payload.get("installed_version"),
            payload.get("latest_version"),
            payload.get("update_available"),
            payload["source_url"],
            payload["status"],
            payload.get("error_message"),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def fetch_history(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    cursor = conn.execute(
        """
        SELECT id, created_at, product, installed_version, latest_version,
               update_available, source_url, status, error_message
        FROM checks
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return list(cursor.fetchall())
