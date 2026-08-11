"""
SQLite-backed event and insight store using Python's built-in sqlite3.
No ORM required — keeps dependencies minimal for the hackathon.
"""
import sqlite3
import json
import os
from typing import Optional

DB_PATH = os.getenv("DB_PATH", "./satellite_insights.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT,
                categories TEXT,
                geometry TEXT,
                status TEXT,
                closed TEXT,
                raw TEXT
            );

            CREATE TABLE IF NOT EXISTS insights (
                event_id TEXT PRIMARY KEY,
                title TEXT,
                brief TEXT,
                imagery_url TEXT,
                hotspot_count INTEGER,
                analysis TEXT,
                categories TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    print(f"[DB] Initialized SQLite at {DB_PATH}")


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def save_event(event: dict):
    """Upsert an EONET event dict into the local DB."""
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO events (id, title, categories, geometry, status, closed, raw)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("id"),
                event.get("title"),
                json.dumps([c.get("id") for c in event.get("categories", [])]),
                json.dumps(event.get("geometry", [])),
                event.get("status", "open"),
                event.get("closed"),
                json.dumps(event),
            ),
        )


def get_event(event_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute("SELECT raw FROM events WHERE id = ?", (event_id,)).fetchone()
    if row:
        return json.loads(row["raw"])
    return None


def list_events(category: Optional[str] = None, limit: int = 20) -> list[dict]:
    with _connect() as conn:
        if category:
            rows = conn.execute(
                "SELECT raw FROM events WHERE categories LIKE ? ORDER BY rowid DESC LIMIT ?",
                (f'%"{category}"%', limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT raw FROM events ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
    return [json.loads(r["raw"]) for r in rows]


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------

def save_insight(insight: dict):
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO insights
                (event_id, title, brief, imagery_url, hotspot_count, analysis, categories)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                insight.get("event_id"),
                insight.get("title"),
                insight.get("brief"),
                insight.get("imagery_url"),
                insight.get("hotspot_count", 0),
                json.dumps(insight.get("analysis", {})),
                json.dumps(insight.get("categories", [])),
            ),
        )


def get_insight_for_event(event_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM insights WHERE event_id = ?", (event_id,)
        ).fetchone()
    if row:
        return _row_to_insight(row)
    return None


def list_insights(limit: int = 10) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM insights ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_insight(r) for r in rows]


def _row_to_insight(row: sqlite3.Row) -> dict:
    return {
        "event_id": row["event_id"],
        "title": row["title"],
        "brief": row["brief"],
        "imagery_url": row["imagery_url"],
        "hotspot_count": row["hotspot_count"],
        "analysis": json.loads(row["analysis"] or "{}"),
        "categories": json.loads(row["categories"] or "[]"),
    }
