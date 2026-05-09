"""
core/database.py
────────────────
Lightweight SQLite wrapper for persistent chat history.

Schema
──────
  conversations(id TEXT PK, created_at TEXT, model TEXT, title TEXT)
  messages(id INTEGER PK, conversation_id TEXT FK, role TEXT,
           content TEXT, timestamp TEXT)

Public API
──────────
  save_message(conversation_id, role, content)
  load_conversation(conversation_id) → list[dict]
  list_conversations() → list[dict]
  delete_conversation(conversation_id)
  rename_conversation(conversation_id, new_title)
  search_messages(query) → list[dict]
"""

from __future__ import annotations

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# DB lives inside the project's data/ folder
DB_PATH = Path(__file__).parent.parent / "data" / "jarvis.db"


# ── Connection helper ─────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    return conn


# ── One-time table creation ───────────────────────────────────────────────────

def init_db():
    """Create tables if they don't exist yet. Safe to call repeatedly."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                created_at  TEXT NOT NULL,
                model       TEXT DEFAULT 'llama3.2',
                title       TEXT DEFAULT 'New conversation'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                timestamp       TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_msg_conv
                ON messages(conversation_id);
        """)


# ── Write operations ──────────────────────────────────────────────────────────

def ensure_conversation(conversation_id: str, model: str = "llama3.2"):
    """Create the conversation row if it doesn't exist."""
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO conversations(id, created_at, model) VALUES(?,?,?)",
            (conversation_id, datetime.now().isoformat(), model),
        )


def save_message(conversation_id: str, role: str, content: str, model: str = "llama3.2"):
    """Persist a single message; auto-creates the conversation row if needed."""
    init_db()
    ensure_conversation(conversation_id, model)
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO messages(conversation_id, role, content, timestamp) VALUES(?,?,?,?)",
            (conversation_id, role, content, datetime.now().isoformat()),
        )
        # Auto-title from the first user message
        first_user = conn.execute(
            "SELECT content FROM messages WHERE conversation_id=? AND role='user' LIMIT 1",
            (conversation_id,),
        ).fetchone()
        if first_user:
            title = first_user["content"][:60].strip().replace("\n", " ")
            conn.execute(
                "UPDATE conversations SET title=? WHERE id=?",
                (title, conversation_id),
            )


def rename_conversation(conversation_id: str, new_title: str):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE conversations SET title=? WHERE id=?",
            (new_title, conversation_id),
        )


def delete_conversation(conversation_id: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM conversations WHERE id=?", (conversation_id,))


# ── Read operations ───────────────────────────────────────────────────────────

def load_conversation(conversation_id: str) -> list[dict]:
    """Return all messages for a conversation, oldest-first."""
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM messages "
            "WHERE conversation_id=? ORDER BY id ASC",
            (conversation_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_conversations(limit: int = 50) -> list[dict]:
    """Return recent conversations (newest first)."""
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, model FROM conversations "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def search_messages(query: str) -> list[dict]:
    """Full-text search across all messages (case-insensitive)."""
    init_db()
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT m.role, m.content, m.timestamp, c.title "
            "FROM messages m JOIN conversations c ON m.conversation_id=c.id "
            "WHERE m.content LIKE ? ORDER BY m.id DESC LIMIT 30",
            (f"%{query}%",),
        ).fetchall()
    return [dict(r) for r in rows]


# Initialise on import
init_db()
