import time
import json
from datetime import datetime, timedelta
from collections import defaultdict
from .database import get_db


class Analytics:
    def __init__(self):
        self._init_tables()
        self.realtime = defaultdict(int)
        self.latencies = []

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                user_id TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                duration_ms REAL,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON analytics_events(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_time ON api_metrics(created_at)")
        conn.commit()
        conn.close()

    def track_event(self, event_type: str, user_id: str = None, data: dict = None):
        self.realtime[event_type] += 1
        conn = get_db()
        conn.execute("""
            INSERT INTO analytics_events (event_type, user_id, data)
            VALUES (?, ?, ?)
        """, (event_type, user_id, json.dumps(data) if data else None))
        conn.commit()
        conn.close()

    def track_api_call(self, endpoint: str, method: str, status_code: int,
                       duration_ms: float, user_id: str = None):
        self.latencies.append(duration_ms)
        if len(self.latencies) > 1000:
            self.latencies = self.latencies[-500:]

        conn = get_db()
        conn.execute("""
            INSERT INTO api_metrics (endpoint, method, status_code, duration_ms, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (endpoint, method, status_code, duration_ms, user_id))
        conn.commit()
        conn.close()

    def get_dashboard(self) -> dict:
        conn = get_db()
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(weeks=1)

        total_events = conn.execute(
            "SELECT COUNT(*) as c FROM analytics_events"
        ).fetchone()["c"]

        events_24h = conn.execute(
            "SELECT COUNT(*) as c FROM analytics_events WHERE created_at > ?",
            (day_ago.isoformat(),)
        ).fetchone()["c"]

        events_1h = conn.execute(
            "SELECT COUNT(*) as c FROM analytics_events WHERE created_at > ?",
            (hour_ago.isoformat(),)
        ).fetchone()["c"]

        unique_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as c FROM analytics_events WHERE created_at > ?",
            (day_ago.isoformat(),)
        ).fetchone()["c"]

        event_types = conn.execute("""
            SELECT event_type, COUNT(*) as count
            FROM analytics_events WHERE created_at > ?
            GROUP BY event_type ORDER BY count DESC LIMIT 10
        """, (day_ago.isoformat(),)).fetchall()

        avg_latency = conn.execute(
            "SELECT AVG(duration_ms) as avg FROM api_metrics WHERE created_at > ?",
            (day_ago.isoformat(),)
        ).fetchone()["avg"] or 0

        error_count = conn.execute(
            "SELECT COUNT(*) as c FROM api_metrics WHERE status_code >= 400 AND created_at > ?",
            (day_ago.isoformat(),)
        ).fetchone()["c"]

        total_api_calls = conn.execute(
            "SELECT COUNT(*) as c FROM api_metrics WHERE created_at > ?",
            (day_ago.isoformat(),)
        ).fetchone()["c"]

        conn.close()

        return {
            "total_events": total_events,
            "events_24h": events_24h,
            "events_1h": events_1h,
            "unique_users_24h": unique_users,
            "event_breakdown": {r["event_type"]: r["count"] for r in event_types},
            "api_metrics": {
                "avg_latency_ms": round(avg_latency, 2),
                "total_calls_24h": total_api_calls,
                "errors_24h": error_count,
                "error_rate": round(error_count / max(total_api_calls, 1) * 100, 2),
            },
            "realtime": dict(self.realtime),
            "current_avg_latency": (
                round(sum(self.latencies) / len(self.latencies), 2)
                if self.latencies else 0
            ),
        }

    def get_hourly_stats(self, hours: int = 24) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT strftime('%Y-%m-%d %H:00', created_at) as hour,
                   COUNT(*) as calls,
                   AVG(duration_ms) as avg_latency
            FROM api_metrics
            WHERE created_at > datetime('now', ?)
            GROUP BY hour ORDER BY hour
        """, (f"-{hours} hours",)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_error_report(self, limit: int = 50) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT endpoint, method, status_code, duration_ms, user_id, created_at
            FROM api_metrics
            WHERE status_code >= 400
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user_activity(self, user_id: str) -> dict:
        conn = get_db()
        total = conn.execute(
            "SELECT COUNT(*) as c FROM analytics_events WHERE user_id=?",
            (user_id,)
        ).fetchone()["c"]

        events = conn.execute("""
            SELECT event_type, COUNT(*) as count
            FROM analytics_events WHERE user_id=?
            GROUP BY event_type ORDER BY count DESC
        """, (user_id,)).fetchall()

        last_active = conn.execute(
            "SELECT MAX(created_at) as last FROM analytics_events WHERE user_id=?",
            (user_id,)
        ).fetchone()["last"]

        conn.close()
        return {
            "user_id": user_id,
            "total_events": total,
            "event_breakdown": {r["event_type"]: r["count"] for r in events},
            "last_active": last_active,
        }
