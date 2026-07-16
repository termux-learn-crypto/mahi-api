import sqlite3
import json
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "mahi.db"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_count INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            emotion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            user_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)
    """)

    conn.commit()
    conn.close()


def save_user(user_id: str, name: str = None):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO users (user_id, name, last_active)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (user_id, name))
    conn.commit()
    conn.close()


def update_user(user_id: str, name: str = None, increment_messages: bool = False):
    conn = get_db()
    if name:
        conn.execute("""
            UPDATE users SET name = ?, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (name, user_id))
    if increment_messages:
        conn.execute("""
            UPDATE users SET message_count = message_count + 1, last_active = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))
    conn.commit()
    conn.close()


def save_message(user_id: str, role: str, content: str, intent: str = None, emotion: str = None):
    conn = get_db()
    conn.execute("""
        INSERT INTO messages (user_id, role, content, intent, emotion)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, role, content, intent, emotion))
    conn.commit()
    conn.close()


def get_messages(user_id: str, limit: int = 50, offset: int = 0) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT role, content, intent, emotion, created_at
        FROM messages
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (user_id, limit, offset)).fetchall()
    conn.close()
    return [dict(row) for row in reversed(rows)]


def get_recent_messages(user_id: str, limit: int = 20) -> list[dict]:
    return get_messages(user_id, limit=limit)


def save_session(user_id: str, session_data: dict):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO sessions (user_id, data, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (user_id, json.dumps(session_data)))
    conn.commit()
    conn.close()


def load_session(user_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("""
        SELECT data FROM sessions WHERE user_id = ?
    """, (user_id,)).fetchone()
    conn.close()
    if row:
        return json.loads(row["data"])
    return None


def delete_session(user_id: str) -> bool:
    conn = get_db()
    cursor = conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_user_stats(user_id: str) -> dict:
    conn = get_db()
    user = conn.execute("""
        SELECT * FROM users WHERE user_id = ?
    """, (user_id,)).fetchone()

    msg_count = conn.execute("""
        SELECT COUNT(*) as count FROM messages WHERE user_id = ?
    """, (user_id,)).fetchone()["count"]

    today_count = conn.execute("""
        SELECT COUNT(*) as count FROM messages
        WHERE user_id = ? AND DATE(created_at) = DATE('now')
    """, (user_id,)).fetchone()["count"]

    top_intents = conn.execute("""
        SELECT intent, COUNT(*) as count
        FROM messages
        WHERE user_id = ? AND intent IS NOT NULL
        GROUP BY intent
        ORDER BY count DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    return {
        "user_id": user_id,
        "name": user["name"] if user else None,
        "total_messages": msg_count,
        "today_messages": today_count,
        "top_intents": [{"intent": r["intent"], "count": r["count"]} for r in top_intents],
        "created_at": user["created_at"] if user else None,
        "last_active": user["last_active"] if user else None,
    }


def get_all_users(limit: int = 100) -> list[dict]:
    conn = get_db()
    rows = conn.execute("""
        SELECT user_id, name, message_count, last_active
        FROM users
        ORDER BY last_active DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


init_db()
