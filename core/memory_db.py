"""
Feature 2: Eternal Memory — Cross-Session Persistent NPC Memory
================================================================
Uses SQLite to store NPC memories permanently across game sessions.
Every NPC builds a personal "journal" of interactions with every player.

Tables:
  - conversations : Full message history per (session_id, npc_name)
  - player_facts  : Extracted facts about the player (e.g. "stole sword", "helped villagers")
  - events        : Significant game events the NPC witnessed or heard about
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "npc_memory.db")


_conn = None

def _get_connection() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def initialize_database():
    """Creates all tables if they don't already exist. Safe to call multiple times."""
    with _get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT    NOT NULL,
                npc_name     TEXT    NOT NULL,
                role         TEXT    NOT NULL,   -- 'user' or 'assistant'
                content      TEXT    NOT NULL,
                game_time    TEXT,               -- optional in-game timestamp
                created_at   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS player_facts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT    NOT NULL,
                npc_name     TEXT    NOT NULL,
                fact         TEXT    NOT NULL,   -- e.g. "player stole a sword from the forge"
                sentiment    TEXT    DEFAULT 'neutral',
                created_at   TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS npc_events (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                npc_name     TEXT    NOT NULL,
                event        TEXT    NOT NULL,
                source       TEXT    DEFAULT 'witnessed',  -- 'witnessed' or 'gossip'
                created_at   TEXT    DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id, npc_name);
            CREATE INDEX IF NOT EXISTS idx_facts_session ON player_facts(session_id, npc_name);
            CREATE INDEX IF NOT EXISTS idx_events_npc ON npc_events(npc_name);
        """)
    print("Database initialized.")


def save_message(session_id: str, npc_name: str, role: str, content: str, game_time: Optional[str] = None):
    """Persists a single conversation turn to the database."""
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO conversations (session_id, npc_name, role, content, game_time) VALUES (?, ?, ?, ?, ?)",
            (session_id, npc_name, role, content, game_time)
        )


def load_history(session_id: str, npc_name: str, max_turns: int = 20) -> list[dict]:
    """
    Loads the last N conversation turns for a session.
    This replaces the old in-memory dict and survives server restarts.
    """
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT role, content FROM conversations
               WHERE session_id = ? AND npc_name = ?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, npc_name, max_turns)
        ).fetchall()
    # Return in chronological order (reverse of DESC query)
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def save_player_fact(session_id: str, npc_name: str, fact: str, sentiment: str = "neutral"):
    """
    Stores an extracted fact about the player.
    The API can call this after notable events (a fight, a theft, a heroic act).
    """
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO player_facts (session_id, npc_name, fact, sentiment) VALUES (?, ?, ?, ?)",
            (session_id, npc_name, fact, sentiment)
        )


def load_player_facts(session_id: str, npc_name: str, limit: int = 5) -> list[str]:
    """Returns the most recent facts this NPC knows about this player."""
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT fact FROM player_facts
               WHERE session_id = ? AND npc_name = ?
               ORDER BY created_at DESC LIMIT ?""",
            (session_id, npc_name, limit)
        ).fetchall()
    return [r["fact"] for r in rows]


def save_event(npc_name: str, event: str, source: str = "witnessed"):
    """Records an event into an NPC's memory (direct witness or gossip)."""
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO npc_events (npc_name, event, source) VALUES (?, ?, ?)",
            (npc_name, event, source)
        )


def load_npc_events(npc_name: str, limit: int = 3) -> list[str]:
    """Returns recent events this NPC has witnessed or heard about."""
    with _get_connection() as conn:
        rows = conn.execute(
            """SELECT event, source FROM npc_events
               WHERE npc_name = ?
               ORDER BY created_at DESC LIMIT ?""",
            (npc_name, limit)
        ).fetchall()
    return [f"[{'Witnessed' if r['source']=='witnessed' else 'Heard'}]: {r['event']}" for r in rows]


def delete_session(session_id: str, npc_name: str):
    """Clears conversation history for one session without deleting facts or events."""
    with _get_connection() as conn:
        conn.execute(
            "DELETE FROM conversations WHERE session_id = ? AND npc_name = ?",
            (session_id, npc_name)
        )


def get_session_summary(session_id: str, npc_name: str) -> dict:
    """Returns a quick summary of a session for debugging."""
    with _get_connection() as conn:
        turn_count = conn.execute(
            "SELECT COUNT(*) as c FROM conversations WHERE session_id=? AND npc_name=?",
            (session_id, npc_name)
        ).fetchone()["c"]
        fact_count = conn.execute(
            "SELECT COUNT(*) as c FROM player_facts WHERE session_id=? AND npc_name=?",
            (session_id, npc_name)
        ).fetchone()["c"]
    return {"turns": turn_count, "known_facts": fact_count}
