"""
SQLite memory — conversation history + always-allow + agent notes.
DB location: ~/.aashoo/memory.db
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".aashoo" / "memory.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tables create karo agar nahi hain."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                last_opened TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS always_allow (
                project_path TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                PRIMARY KEY (project_path, tool_name)
            );

            CREATE TABLE IF NOT EXISTS agent_notes (
                project_path TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (project_path, key)
            );
        """)


def upsert_project(name: str, path: str):
    """Project register karo ya last_opened update karo."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO projects (name, path, last_opened)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(path) DO UPDATE SET
                last_opened = datetime('now')
        """, (name, path))


def save_message(project_path: str, role: str, content: str):
    """Ek message save karo."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (project_path, role, content) VALUES (?, ?, ?)",
            (project_path, role, content)
        )


def load_history(project_path: str, limit: int = 50) -> list[dict]:
    """Last N messages load karo LLM ke format mein."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT role, content FROM messages
            WHERE project_path = ?
            ORDER BY id DESC LIMIT ?
        """, (project_path, limit)).fetchall()

    # Reverse karo — oldest first
    history = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    return history


def clear_history(project_path: str):
    """Project ki saari history delete karo."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM messages WHERE project_path = ?",
            (project_path,)
        )


def is_always_allowed(project_path: str, tool_name: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT 1 FROM always_allow
            WHERE project_path = ? AND tool_name = ?
        """, (project_path, tool_name)).fetchone()
    return row is not None


def set_always_allow(project_path: str, tool_name: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO always_allow (project_path, tool_name)
            VALUES (?, ?)
        """, (project_path, tool_name))


def save_note(project_path: str, key: str, value: str):
    """Agent ka note save karo (e.g. 'main_language': 'python')."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO agent_notes (project_path, key, value, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(project_path, key) DO UPDATE SET
                value = excluded.value,
                updated_at = datetime('now')
        """, (project_path, key, value))


def get_note(project_path: str, key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT value FROM agent_notes
            WHERE project_path = ? AND key = ?
        """, (project_path, key)).fetchone()
    return row["value"] if row else None


# DB initialize karo import hone par
init_db()