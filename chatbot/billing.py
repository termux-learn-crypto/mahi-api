import json
from datetime import datetime, timedelta
from .database import get_db


class BillingEngine:
    PLANS = {
        "free": {
            "name": "Free",
            "price": 0,
            "requests_per_day": 100,
            "plugins": ["weather", "news", "notes", "todo", "calculator"],
            "features": ["basic_chat", "memory", "context"],
        },
        "pro": {
            "name": "Pro",
            "price": 99,
            "requests_per_day": 1000,
            "plugins": "all",
            "features": ["basic_chat", "memory", "context", "voice", "analytics", "knowledge"],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 999,
            "requests_per_day": 10000,
            "plugins": "all",
            "features": ["basic_chat", "memory", "context", "voice", "analytics", "knowledge",
                        "multi_tenant", "priority_support", "custom_plugins"],
        },
    }

    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                requests INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                api_calls INTEGER DEFAULT 0,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS billing_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                amount REAL NOT NULL,
                plan TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                period_start TEXT,
                period_end TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def track_usage(self, tenant_id: str, requests: int = 1, tokens: int = 0):
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_db()

        existing = conn.execute(
            "SELECT id FROM billing_usage WHERE tenant_id=? AND date=?",
            (tenant_id, today)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE billing_usage SET requests=requests+?, tokens_used=tokens_used+?
                WHERE id=?
            """, (requests, tokens, existing["id"]))
        else:
            conn.execute("""
                INSERT INTO billing_usage (tenant_id, requests, tokens_used, date)
                VALUES (?, ?, ?, ?)
            """, (tenant_id, requests, tokens, today))

        conn.commit()
        conn.close()

    def check_limits(self, tenant_id: str) -> dict:
        from .tenant import tenant_manager
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {"allowed": False, "reason": "Tenant not found"}

        plan = self.PLANS.get(tenant["plan"], self.PLANS["free"])
        today = datetime.now().strftime("%Y-%m-%d")

        conn = get_db()
        usage = conn.execute(
            "SELECT requests FROM billing_usage WHERE tenant_id=? AND date=?",
            (tenant_id, today)
        ).fetchone()
        conn.close()

        today_requests = usage["requests"] if usage else 0
        limit = plan["requests_per_day"]

        return {
            "allowed": today_requests < limit,
            "plan": tenant["plan"],
            "used": today_requests,
            "limit": limit,
            "remaining": max(0, limit - today_requests),
        }

    def get_usage(self, tenant_id: str, days: int = 30) -> dict:
        conn = get_db()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        rows = conn.execute("""
            SELECT date, requests, tokens_used
            FROM billing_usage WHERE tenant_id=? AND date>=?
            ORDER BY date
        """, (tenant_id, cutoff)).fetchall()
        conn.close()

        total_requests = sum(r["requests"] for r in rows)
        total_tokens = sum(r["tokens_used"] for r in rows)

        from .tenant import tenant_manager
        tenant = tenant_manager.get_tenant(tenant_id)
        plan_name = tenant["plan"] if tenant else "free"
        plan = self.PLANS.get(plan_name, self.PLANS["free"])

        estimated_cost = 0
        if plan["price"] > 0:
            estimated_cost = plan["price"]

        return {
            "tenant_id": tenant_id,
            "plan": plan_name,
            "period_days": days,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "daily_usage": [
                {"date": r["date"], "requests": r["requests"], "tokens": r["tokens_used"]}
                for r in rows
            ],
            "estimated_cost": estimated_cost,
        }

    def create_invoice(self, tenant_id: str) -> dict:
        from .tenant import tenant_manager
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}

        plan = self.PLANS.get(tenant["plan"], self.PLANS["free"])

        period_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        period_end = datetime.now().strftime("%Y-%m-%d")

        conn = get_db()
        cursor = conn.execute("""
            INSERT INTO billing_invoices (tenant_id, amount, plan, period_start, period_end)
            VALUES (?, ?, ?, ?, ?)
        """, (tenant_id, plan["price"], tenant["plan"], period_start, period_end))
        invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "invoice_id": invoice_id,
            "tenant_id": tenant_id,
            "amount": plan["price"],
            "plan": tenant["plan"],
            "period": f"{period_start} to {period_end}",
            "status": "pending",
        }

    def get_invoices(self, tenant_id: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT * FROM billing_invoices WHERE tenant_id=?
            ORDER BY created_at DESC LIMIT 12
        """, (tenant_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_plan_details(self, plan_name: str) -> dict:
        return self.PLANS.get(plan_name, self.PLANS["free"])

    def get_all_plans(self) -> dict:
        return self.PLANS


billing = BillingEngine()
