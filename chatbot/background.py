import threading
import time
from datetime import datetime
from collections import defaultdict
from .database import get_db


class BackgroundProcessor:
    def __init__(self):
        self.tasks = {}
        self.results = {}
        self.lock = threading.Lock()
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS background_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                user_id TEXT,
                task_type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def submit_task(self, user_id: str, task_type: str, params: dict = None) -> str:
        import uuid
        task_id = str(uuid.uuid4())[:8]

        conn = get_db()
        conn.execute("""
            INSERT INTO background_tasks (task_id, user_id, task_type, status)
            VALUES (?, ?, ?, 'pending')
        """, (task_id, user_id, task_type))
        conn.commit()
        conn.close()

        with self.lock:
            self.tasks[task_id] = {
                "user_id": user_id,
                "type": task_type,
                "params": params or {},
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }

        thread = threading.Thread(target=self._process_task, args=(task_id,))
        thread.daemon = True
        thread.start()

        return task_id

    def _process_task(self, task_id: str):
        with self.lock:
            if task_id not in self.tasks:
                return
            self.tasks[task_id]["status"] = "running"
            self.tasks[task_id]["started_at"] = datetime.now().isoformat()

        conn = get_db()
        conn.execute(
            "UPDATE background_tasks SET status='running', started_at=CURRENT_TIMESTAMP WHERE task_id=?",
            (task_id,)
        )
        conn.commit()
        conn.close()

        try:
            task = self.tasks[task_id]
            result = self._execute_task(task["type"], task["params"])

            with self.lock:
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["completed_at"] = datetime.now().isoformat()

            conn = get_db()
            conn.execute("""
                UPDATE background_tasks SET status='completed', result=?, completed_at=CURRENT_TIMESTAMP
                WHERE task_id=?
            """, (str(result), task_id))
            conn.commit()
            conn.close()

        except Exception as e:
            with self.lock:
                self.tasks[task_id]["status"] = "failed"
                self.tasks[task_id]["result"] = {"error": str(e)}

            conn = get_db()
            conn.execute(
                "UPDATE background_tasks SET status='failed', result=? WHERE task_id=?",
                (str({"error": str(e)}), task_id)
            )
            conn.commit()
            conn.close()

    def _execute_task(self, task_type: str, params: dict) -> dict:
        if task_type == "memory_consolidate":
            from .memory import MemorySystem
            memory = MemorySystem()
            return memory.consolidate_memories(params.get("user_id", "system"))

        elif task_type == "knowledge_extract":
            from .knowledge_graph import knowledge_graph
            return knowledge_graph.extract_from_text(
                params.get("user_id", "system"),
                params.get("text", "")
            )

        elif task_type == "analytics_report":
            from .analytics import Analytics
            analytics = Analytics()
            return analytics.get_trend_report(params.get("days", 7))

        elif task_type == "memory_decay":
            from .memory import MemorySystem
            memory = MemorySystem()
            return {"decayed": memory.apply_decay()}

        elif task_type == "process_queue":
            from .offline import offline
            return offline.get_offline_stats()

        return {"status": "unknown_task_type"}

    def get_task_status(self, task_id: str) -> dict:
        with self.lock:
            if task_id in self.tasks:
                return {
                    "task_id": task_id,
                    **self.tasks[task_id],
                }

        conn = get_db()
        row = conn.execute(
            "SELECT * FROM background_tasks WHERE task_id=?", (task_id,)
        ).fetchone()
        conn.close()

        if row:
            return {
                "task_id": row["task_id"],
                "user_id": row["user_id"],
                "type": row["task_type"],
                "status": row["status"],
                "result": row["result"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
            }
        return {"error": "Task not found"}

    def get_user_tasks(self, user_id: str, limit: int = 20) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT task_id, task_type, status, created_at, completed_at
            FROM background_tasks WHERE user_id=?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        conn = get_db()
        total = conn.execute("SELECT COUNT(*) as c FROM background_tasks").fetchone()["c"]
        running = conn.execute(
            "SELECT COUNT(*) as c FROM background_tasks WHERE status='running'"
        ).fetchone()["c"]
        completed = conn.execute(
            "SELECT COUNT(*) as c FROM background_tasks WHERE status='completed'"
        ).fetchone()["c"]
        failed = conn.execute(
            "SELECT COUNT(*) as c FROM background_tasks WHERE status='failed'"
        ).fetchone()["c"]
        conn.close()
        return {"total": total, "running": running, "completed": completed, "failed": failed}


background = BackgroundProcessor()
