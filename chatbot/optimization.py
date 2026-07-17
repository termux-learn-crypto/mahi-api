import time
from datetime import datetime, timedelta
from collections import defaultdict
from .database import get_db


class BatteryOptimizer:
    def __init__(self):
        self._init_tables()
        self.strategies = {
            "batch_requests": True,
            "compress_responses": True,
            "cache_frequent": True,
            "reduce_analytics": False,
            "lazy_loading": True,
        }

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS optimization_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                strategy TEXT,
                savings_ms REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def optimize_response(self, response: dict, user_id: str = None) -> dict:
        if self.strategies["compress_responses"]:
            response = self._compress_response(response)

        if self.strategies["cache_frequent"] and user_id:
            self._update_access_pattern(user_id)

        return response

    def _compress_response(self, response: dict) -> dict:
        compressed = {}

        for key, value in response.items():
            if isinstance(value, str) and len(value) > 500:
                compressed[key] = value[:500] + "..."
            elif isinstance(value, list) and len(value) > 10:
                compressed[key] = value[:10]
                compressed[f"{key}_truncated"] = True
            else:
                compressed[key] = value

        return compressed

    def _update_access_pattern(self, user_id: str):
        conn = get_db()
        conn.execute("""
            INSERT INTO optimization_stats (user_id, strategy, savings_ms)
            VALUES (?, 'access_pattern', 0)
        """, (user_id,))
        conn.commit()
        conn.close()

    def should_batch(self, user_id: str) -> bool:
        if not self.strategies["batch_requests"]:
            return False

        conn = get_db()
        recent = conn.execute("""
            SELECT COUNT(*) as c FROM optimization_stats
            WHERE user_id=? AND created_at > datetime('now', '-1 minute')
        """, (user_id,)).fetchone()["c"]
        conn.close()

        return recent > 3

    def get_battery_tips(self) -> list[dict]:
        return [
            {
                "tip": "Batch API requests",
                "description": "Combine multiple small requests into one",
                "savings": "Up to 30% battery",
            },
            {
                "tip": "Use caching",
                "description": "Cache frequent responses locally",
                "savings": "Up to 25% battery",
            },
            {
                "tip": "Reduce polling frequency",
                "description": "Use WebSocket instead of polling",
                "savings": "Up to 40% battery",
            },
            {
                "tip": "Compress responses",
                "description": "Use gzip/brotli compression",
                "savings": "Up to 15% battery",
            },
            {
                "tip": "Lazy load data",
                "description": "Load data only when needed",
                "savings": "Up to 20% battery",
            },
        ]

    def get_optimization_stats(self, user_id: str = None) -> dict:
        conn = get_db()

        if user_id:
            total_savings = conn.execute(
                "SELECT SUM(savings_ms) as total FROM optimization_stats WHERE user_id=?",
                (user_id,)
            ).fetchone()["total"] or 0

            strategy_usage = conn.execute("""
                SELECT strategy, COUNT(*) as count, SUM(savings_ms) as savings
                FROM optimization_stats WHERE user_id=?
                GROUP BY strategy
            """, (user_id,)).fetchall()
        else:
            total_savings = conn.execute(
                "SELECT SUM(savings_ms) as total FROM optimization_stats"
            ).fetchone()["total"] or 0

            strategy_usage = conn.execute("""
                SELECT strategy, COUNT(*) as count, SUM(savings_ms) as savings
                FROM optimization_stats
                GROUP BY strategy
            """).fetchall()

        conn.close()

        return {
            "strategies": self.strategies,
            "total_savings_ms": round(total_savings, 2),
            "strategy_usage": {
                r["strategy"]: {"count": r["count"], "savings": round(r["savings"], 2)}
                for r in strategy_usage
            },
        }

    def update_strategy(self, strategy: str, enabled: bool) -> dict:
        if strategy in self.strategies:
            self.strategies[strategy] = enabled
            return {"strategy": strategy, "enabled": enabled}
        return {"error": f"Unknown strategy: {strategy}"}


optimizer = BatteryOptimizer()
