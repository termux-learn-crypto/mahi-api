import json
import time
import math
from datetime import datetime, timedelta
from collections import defaultdict
from difflib import SequenceMatcher
from .database import get_db


class MemorySystem:
    SHORT_TERM_LIMIT = 20
    LONG_TERM_THRESHOLD = 0.7
    DECAY_RATE = 0.05
    CONSOLIDATION_THRESHOLD = 3

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
                consolidated INTEGER DEFAULT 0,
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

        try:
            conn.execute("ALTER TABLE memories ADD COLUMN consolidated INTEGER DEFAULT 0")
        except Exception:
            pass

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

    def search_semantic(self, user_id: str, query: str, limit: int = 10) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, memory_type, content, importance, context, created_at, accessed_at
            FROM memories WHERE user_id = ?
            ORDER BY importance DESC, accessed_at DESC
            LIMIT 200
        """, (user_id,)).fetchall()
        conn.close()

        scored = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for row in rows:
            content = row["content"].lower()
            content_words = set(content.split())

            word_overlap = len(query_words & content_words) / max(len(query_words), 1)
            similarity = SequenceMatcher(None, query_lower, content).ratio()
            fuzzy_bonus = 0.2 if any(
                SequenceMatcher(None, query_lower, content_word).ratio() > 0.7
                for content_word in content_words
            ) else 0

            score = (word_overlap * 0.4) + (similarity * 0.4) + (fuzzy_bonus * 0.2)
            score *= row["importance"]

            if score > 0.05:
                scored.append({
                    **dict(row),
                    "relevance": round(score, 3),
                })

        scored.sort(key=lambda x: x["relevance"], reverse=True)
        return scored[:limit]

    def apply_decay(self, user_id: str = None):
        conn = get_db()

        if user_id:
            rows = conn.execute(
                "SELECT id, importance, accessed_at FROM memories WHERE user_id=?",
                (user_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, importance, accessed_at FROM memories"
            ).fetchall()

        now = datetime.now()
        updated = 0

        for row in rows:
            if row["accessed_at"]:
                try:
                    accessed = datetime.fromisoformat(row["accessed_at"])
                    days_since = (now - accessed).days
                except (ValueError, TypeError):
                    days_since = 0
            else:
                days_since = 0

            if days_since > 0:
                decay = math.exp(-self.DECAY_RATE * days_since)
                new_importance = max(0.1, row["importance"] * decay)

                if abs(new_importance - row["importance"]) > 0.01:
                    conn.execute(
                        "UPDATE memories SET importance=? WHERE id=?",
                        (round(new_importance, 3), row["id"])
                    )
                    updated += 1

        conn.commit()
        conn.close()
        return updated

    def consolidate_memories(self, user_id: str) -> dict:
        conn = get_db()

        rows = conn.execute("""
            SELECT id, content, importance, created_at
            FROM memories WHERE user_id=? AND memory_type='short_term' AND consolidated=0
            ORDER BY created_at
        """, (user_id,)).fetchall()

        if len(rows) < self.CONSOLIDATION_THRESHOLD:
            conn.close()
            return {"consolidated": 0, "merged": 0}

        groups = self._group_similar_memories(rows)

        consolidated = 0
        merged = 0

        for group in groups:
            if len(group) >= 2:
                combined_content = " | ".join([r["content"] for r in group[:5]])
                avg_importance = sum(r["importance"] for r in group) / len(group)
                max_importance = max(r["importance"] for r in group)
                final_importance = min(1.0, (avg_importance + max_importance) / 2 + 0.1)

                conn.execute("""
                    INSERT INTO memories (user_id, memory_type, content, importance, context)
                    VALUES (?, 'long_term', ?, ?, ?)
                """, (user_id, combined_content, final_importance,
                      json.dumps({"consolidated_from": [r["id"] for r in group]})))

                for r in group:
                    conn.execute("UPDATE memories SET consolidated=1 WHERE id=?", (r["id"],))
                    consolidated += 1

                merged += 1

        conn.commit()
        conn.close()
        return {"consolidated": consolidated, "merged": merged}

    def _group_similar_memories(self, rows: list) -> list[list]:
        groups = []
        used = set()

        for i, row in enumerate(rows):
            if i in used:
                continue

            group = [row]
            used.add(i)

            for j, other in enumerate(rows):
                if j in used:
                    continue

                sim = SequenceMatcher(None, row["content"], other["content"]).ratio()
                if sim > 0.6:
                    group.append(other)
                    used.add(j)

            groups.append(group)

        return groups

    def get_memory_timeline(self, user_id: str, days: int = 7) -> list[dict]:
        conn = get_db()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        rows = conn.execute("""
            SELECT id, memory_type, content, importance, created_at
            FROM memories WHERE user_id=? AND created_at > ?
            ORDER BY created_at
        """, (user_id, cutoff)).fetchall()
        conn.close()

        daily = defaultdict(list)
        for row in rows:
            try:
                date = datetime.fromisoformat(row["created_at"]).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                date = "unknown"
            daily[date].append({
                "id": row["id"],
                "type": row["memory_type"],
                "content": row["content"][:100],
                "importance": row["importance"],
            })

        return [
            {"date": date, "memories": memories, "count": len(memories)}
            for date, memories in sorted(daily.items())
        ]

    def get_memory_insights(self, user_id: str) -> dict:
        conn = get_db()

        type_stats = conn.execute("""
            SELECT memory_type, COUNT(*) as count, AVG(importance) as avg_importance,
                   MAX(accessed_at) as last_accessed
            FROM memories WHERE user_id=?
            GROUP BY memory_type
        """, (user_id,)).fetchall()

        old_memories = conn.execute("""
            SELECT COUNT(*) as c FROM memories WHERE user_id=?
            AND importance < 0.3
        """, (user_id,)).fetchone()["c"]

        frequently_accessed = conn.execute("""
            SELECT COUNT(*) as c FROM memories WHERE user_id=?
            AND access_count > 5
        """, (user_id,)).fetchone()["c"]

        conn.close()

        return {
            "type_statistics": {
                r["memory_type"]: {
                    "count": r["count"],
                    "avg_importance": round(r["avg_importance"], 3),
                    "last_accessed": r["last_accessed"],
                }
                for r in type_stats
            },
            "fading_memories": old_memories,
            "frequently_accessed": frequently_accessed,
            "health_score": self._calculate_memory_health(type_stats, old_memories, frequently_accessed),
        }

    def _calculate_memory_health(self, type_stats: list, old: int, frequent: int) -> float:
        total = sum(r["count"] for r in type_stats) or 1
        variety = len(type_stats) / 3
        recency = 1 - (old / total)
        engagement = frequent / total

        score = (variety * 0.3 + recency * 0.4 + engagement * 0.3)
        return round(min(1.0, score), 2)
