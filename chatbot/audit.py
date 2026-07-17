import json
from datetime import datetime
from .database import get_db


class AuditTrail:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at)
        """)
        conn.commit()
        conn.close()

    def log_action(self, user_id: str, action: str, resource: str = None,
                   details: dict = None, ip_address: str = None,
                   user_agent: str = None, status: str = "success") -> dict:
        conn = get_db()
        conn.execute("""
            INSERT INTO audit_logs (user_id, action, resource, details, ip_address, user_agent, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, action, resource, json.dumps(details) if details else None,
              ip_address, user_agent, status))
        conn.commit()
        conn.close()
        return {"logged": True, "action": action, "user_id": user_id}

    def get_user_logs(self, user_id: str, limit: int = 100) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT action, resource, details, status, created_at
            FROM audit_logs WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_action_logs(self, action: str, limit: int = 100) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT user_id, resource, details, status, created_at
            FROM audit_logs WHERE action=?
            ORDER BY created_at DESC LIMIT ?
        """, (action, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_recent_logs(self, hours: int = 24, limit: int = 200) -> list[dict]:
        conn = get_db()
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        rows = conn.execute("""
            SELECT user_id, action, resource, status, created_at
            FROM audit_logs WHERE created_at > ?
            ORDER BY created_at DESC LIMIT ?
        """, (cutoff, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_security_events(self, hours: int = 24) -> list[dict]:
        security_actions = [
            "login", "logout", "failed_login", "password_change",
            "api_key_created", "api_key_revoked", "data_export", "data_delete",
            "permission_change", "admin_action",
        ]

        conn = get_db()
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        placeholders = ",".join(["?"] * len(security_actions))
        rows = conn.execute(f"""
            SELECT user_id, action, resource, details, status, created_at
            FROM audit_logs
            WHERE action IN ({placeholders}) AND created_at > ?
            ORDER BY created_at DESC
        """, (*security_actions, cutoff)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user_activity_summary(self, user_id: str) -> dict:
        conn = get_db()

        total = conn.execute(
            "SELECT COUNT(*) as c FROM audit_logs WHERE user_id=?", (user_id,)
        ).fetchone()["c"]

        actions = conn.execute("""
            SELECT action, COUNT(*) as count
            FROM audit_logs WHERE user_id=?
            GROUP BY action ORDER BY count DESC
        """, (user_id,)).fetchall()

        failed = conn.execute(
            "SELECT COUNT(*) as c FROM audit_logs WHERE user_id=? AND status='failed'",
            (user_id,)
        ).fetchone()["c"]

        last_active = conn.execute(
            "SELECT MAX(created_at) as last FROM audit_logs WHERE user_id=?",
            (user_id,)
        ).fetchone()["last"]

        conn.close()

        return {
            "user_id": user_id,
            "total_actions": total,
            "failed_actions": failed,
            "action_breakdown": {r["action"]: r["count"] for r in actions},
            "last_active": last_active,
        }

    def get_audit_stats(self) -> dict:
        conn = get_db()

        total = conn.execute("SELECT COUNT(*) as c FROM audit_logs").fetchone()["c"]

        from datetime import timedelta
        day_ago = (datetime.now() - timedelta(days=1)).isoformat()
        recent = conn.execute(
            "SELECT COUNT(*) as c FROM audit_logs WHERE created_at > ?", (day_ago,)
        ).fetchone()["c"]

        failed = conn.execute(
            "SELECT COUNT(*) as c FROM audit_logs WHERE status='failed'"
        ).fetchone()["c"]

        unique_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as c FROM audit_logs"
        ).fetchone()["c"]

        conn.close()

        return {
            "total_logs": total,
            "last_24h": recent,
            "failed_actions": failed,
            "unique_users": unique_users,
            "success_rate": round((total - failed) / max(total, 1) * 100, 2),
        }


audit = AuditTrail()
