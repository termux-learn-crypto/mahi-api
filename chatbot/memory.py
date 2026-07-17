import json
import time
from datetime import datetime
from collections import defaultdict
from .database import get_db


class MemorySystem:
    SHORT_TERM_LIMIT = 20
    LONG_TERM_THRESHOLD = 0.7

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, key),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS personal_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fact TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(user_id, memory_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_facts_user ON personal_facts(user_id)")
        conn.commit()
        conn.close()

    def add_memory(self, user_id: str, memory_type: str, content: str,
                   importance: float = 0.5, context: str = None):
        if importance < self.LONG_TERM_THRESHOLD:
            self._trim_short_term(user_id)

        conn = get_db()
        conn.execute("""
            INSERT INTO memories (user_id, memory_type, content, importance, context)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, memory_type, content, importance, context))
        conn.commit()
        conn.close()

    def _trim_short_term(self, user_id: str):
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) as c FROM memories WHERE user_id=? AND memory_type='short_term'",
            (user_id,)
        ).fetchone()["c"]
        if count >= self.SHORT_TERM_LIMIT:
            conn.execute("""
                DELETE FROM memories WHERE user_id=? AND memory_type='short_term'
                AND id IN (
                    SELECT id FROM memories WHERE user_id=? AND memory_type='short_term'
                    ORDER BY accessed_at ASC LIMIT ?
                )
            """, (user_id, user_id, count - self.SHORT_TERM_LIMIT + 1))
            conn.commit()
        conn.close()

    def search_memory(self, user_id: str, query: str, limit: int = 10) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, memory_type, content, importance, context, created_at
            FROM memories
            WHERE user_id = ? AND content LIKE ?
            ORDER BY importance DESC, accessed_at DESC
            LIMIT ?
        """, (user_id, f"%{query}%", limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_memories(self, user_id: str, memory_type: str = None, limit: int = 50) -> list[dict]:
        conn = get_db()
        if memory_type:
            rows = conn.execute("""
                SELECT id, memory_type, content, importance, context, created_at, accessed_at
                FROM memories WHERE user_id = ? AND memory_type = ?
                ORDER BY importance DESC, accessed_at DESC LIMIT ?
            """, (user_id, memory_type, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, memory_type, content, importance, context, created_at, accessed_at
                FROM memories WHERE user_id = ?
                ORDER BY importance DESC, accessed_at DESC LIMIT ?
            """, (user_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_memory(self, memory_id: int):
        conn = get_db()
        conn.execute("""
            UPDATE memories SET accessed_at = CURRENT_TIMESTAMP,
            access_count = access_count + 1 WHERE id = ?
        """, (memory_id,))
        conn.commit()
        conn.close()

    def delete_memory(self, memory_id: int) -> bool:
        conn = get_db()
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def summarize_memory(self, user_id: str) -> dict:
        conn = get_db()
        total = conn.execute(
            "SELECT COUNT(*) as c FROM memories WHERE user_id=?", (user_id,)
        ).fetchone()["c"]
        by_type = conn.execute("""
            SELECT memory_type, COUNT(*) as count FROM memories
            WHERE user_id=? GROUP BY memory_type
        """, (user_id,)).fetchall()
        important = conn.execute("""
            SELECT content FROM memories WHERE user_id=? AND importance >= 0.8
            ORDER BY importance DESC LIMIT 10
        """, (user_id,)).fetchall()
        conn.close()
        return {
            "total_memories": total,
            "by_type": {r["memory_type"]: r["count"] for r in by_type},
            "important_memories": [r["content"] for r in important],
        }

    def set_preference(self, user_id: str, key: str, value: str):
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, key, value))
        conn.commit()
        conn.close()

    def get_preference(self, user_id: str, key: str) -> str | None:
        conn = get_db()
        row = conn.execute(
            "SELECT value FROM user_preferences WHERE user_id=? AND key=?",
            (user_id, key)
        ).fetchone()
        conn.close()
        return row["value"] if row else None

    def get_all_preferences(self, user_id: str) -> dict:
        conn = get_db()
        rows = conn.execute(
            "SELECT key, value FROM user_preferences WHERE user_id=?",
            (user_id,)
        ).fetchall()
        conn.close()
        return {r["key"]: r["value"] for r in rows}

    def add_personal_fact(self, user_id: str, fact: str,
                          category: str = "general", confidence: float = 1.0, source: str = "user"):
        conn = get_db()
        conn.execute("""
            INSERT INTO personal_facts (user_id, fact, category, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, fact, category, confidence, source))
        conn.commit()
        conn.close()

    def get_personal_facts(self, user_id: str, category: str = None) -> list[dict]:
        conn = get_db()
        if category:
            rows = conn.execute("""
                SELECT id, fact, category, confidence, source, created_at
                FROM personal_facts WHERE user_id=? AND category=?
                ORDER BY confidence DESC
            """, (user_id, category)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, fact, category, confidence, source, created_at
                FROM personal_facts WHERE user_id=?
                ORDER BY confidence DESC
            """, (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def search_personal_facts(self, user_id: str, query: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, fact, category, confidence, source
            FROM personal_facts WHERE user_id=? AND fact LIKE ?
            ORDER BY confidence DESC LIMIT 10
        """, (user_id, f"%{query}%")).fetchall()
        conn.close()
        return [dict(r) for r in rows]
