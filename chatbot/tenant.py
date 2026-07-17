import json
from datetime import datetime
from .database import get_db


class TenantManager:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                settings TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tenant_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)
        conn.commit()
        conn.close()

    def create_tenant(self, tenant_id: str, name: str, plan: str = "free",
                      settings: dict = None) -> dict:
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO tenants (tenant_id, name, plan, settings)
                VALUES (?, ?, ?, ?)
            """, (tenant_id, name, plan, json.dumps(settings or {})))
            conn.commit()
            conn.close()
            return {"created": True, "tenant_id": tenant_id, "name": name, "plan": plan}
        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def get_tenant(self, tenant_id: str) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM tenants WHERE tenant_id=?", (tenant_id,)
        ).fetchone()
        conn.close()

        if not row:
            return None

        return {
            "tenant_id": row["tenant_id"],
            "name": row["name"],
            "plan": row["plan"],
            "settings": json.loads(row["settings"] or "{}"),
            "created_at": row["created_at"],
        }

    def update_tenant(self, tenant_id: str, **kwargs) -> dict:
        conn = get_db()
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in ("name", "plan", "settings"):
                updates.append(f"{key}=?")
                if key == "settings":
                    values.append(json.dumps(value))
                else:
                    values.append(value)

        if not updates:
            conn.close()
            return {"error": "No valid fields to update"}

        updates.append("updated_at=CURRENT_TIMESTAMP")
        values.append(tenant_id)

        conn.execute(
            f"UPDATE tenants SET {', '.join(updates)} WHERE tenant_id=?",
            values
        )
        conn.commit()
        conn.close()
        return {"updated": True, "tenant_id": tenant_id}

    def delete_tenant(self, tenant_id: str) -> dict:
        conn = get_db()
        conn.execute("DELETE FROM tenant_users WHERE tenant_id=?", (tenant_id,))
        conn.execute("DELETE FROM tenants WHERE tenant_id=?", (tenant_id,))
        conn.commit()
        conn.close()
        return {"deleted": True, "tenant_id": tenant_id}

    def add_user_to_tenant(self, tenant_id: str, user_id: str, role: str = "member") -> dict:
        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO tenant_users (tenant_id, user_id, role)
                VALUES (?, ?, ?)
            """, (tenant_id, user_id, role))
            conn.commit()
            conn.close()
            return {"added": True, "tenant_id": tenant_id, "user_id": user_id, "role": role}
        except Exception as e:
            conn.close()
            return {"error": str(e)}

    def remove_user_from_tenant(self, tenant_id: str, user_id: str) -> dict:
        conn = get_db()
        conn.execute(
            "DELETE FROM tenant_users WHERE tenant_id=? AND user_id=?",
            (tenant_id, user_id)
        )
        conn.commit()
        conn.close()
        return {"removed": True, "tenant_id": tenant_id, "user_id": user_id}

    def get_tenant_users(self, tenant_id: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            "SELECT user_id, role, created_at FROM tenant_users WHERE tenant_id=?",
            (tenant_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_user_tenants(self, user_id: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT t.tenant_id, t.name, t.plan, tu.role
            FROM tenants t
            JOIN tenant_users tu ON t.tenant_id = tu.tenant_id
            WHERE tu.user_id=?
        """, (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_all_tenants(self, limit: int = 100) -> list[dict]:
        conn = get_db()
        rows = conn.execute(
            "SELECT tenant_id, name, plan, created_at FROM tenants LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


tenant_manager = TenantManager()
