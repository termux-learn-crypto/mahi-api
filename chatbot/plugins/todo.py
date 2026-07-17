import re
from datetime import datetime
from . import Plugin
from ..database import get_db


class TodoPlugin(Plugin):
    PRIORITY_MAP = {
        "high": 1, "urgent": 1, "jaldi": 1, "important": 1, "zaroori": 1,
        "medium": 2, "normal": 2, "aam": 2,
        "low": 3, "low priority": 3, "baad mein": 3, "kabhi bhi": 3,
    }
    PRIORITY_EMOJI = {1: "🔴", 2: "🟡", 3: "🟢"}
    PRIORITY_LABEL = {1: "High", 2: "Medium", 3: "Low"}

    def __init__(self):
        super().__init__(
            name="todo",
            description="To-do list - add tasks, mark complete, delete, show pending with priorities",
            version="1.0.0",
        )
        self.commands = ["todo", "task", "kaam", "list", "pending"]
        self.keywords = [
            "todo", "task", "kaam", "pending", "pending hai", "done",
            "complete", "pura", "ho gaya", "add task", "naya kaam",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent in ("todo", "task"):
            return True
        msg = message.lower()
        return any(kw in msg for kw in self.keywords)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.strip()
        conn = get_db()

        try:
            if re.search(r'\b(pending|baaki|remaining|dikhao|show|list|sab|saare|all)\b', msg, re.I):
                return self._list_tasks(conn, user_id, msg)
            if re.search(r'\b(done|complete|pura|ho gaya|mark|done karo|khatam)\b', msg, re.I):
                return self._complete_task(conn, user_id, msg)
            if re.search(r'\b(delete|hatao|remove|mita|cancel)\b', msg, re.I):
                return self._delete_task(conn, user_id, msg)
            return self._add_task(conn, user_id, msg)
        finally:
            conn.close()

    def _init_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                task TEXT NOT NULL,
                priority INTEGER DEFAULT 2,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        conn.commit()

    def _add_task(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        priority = 2
        for pkey, pval in self.PRIORITY_MAP.items():
            if pkey in message.lower():
                priority = pval
                break

        task = re.sub(
            r'\b(todo|task|add|karo|naya|please|banao|create|i want|i need|i should|i have to|kaam|high|medium|low|urgent|important|jaldi|zaroori|baad mein|kabhi bhi|normal)\b',
            '', message, flags=re.I
        ).strip()
        task = task.strip('".!?,')
        if not task:
            return {"response": "Kya kaam add karna hai? Task batao! 📋\nPriority: 'high/medium/low' use kar sakte ho."}

        pemoji = self.PRIORITY_EMOJI[priority]
        plabel = self.PRIORITY_LABEL[priority]

        cursor = conn.execute(
            "INSERT INTO todo (user_id, task, priority) VALUES (?, ?, ?)",
            (user_id, task, priority),
        )
        conn.commit()
        task_id = cursor.lastrowid
        return {
            "response": f"{pemoji} Task add ho gaya! (#{task_id})\n\n📝 {task}\n⚡ Priority: {plabel}",
            "data": {"task_id": task_id, "task": task, "priority": priority},
        }

    def _list_tasks(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        show_completed = bool(re.search(r'\b(completed|done|pura|ho gaya|sab|all)\b', message, re.I))

        if show_completed:
            rows = conn.execute(
                "SELECT id, task, priority, completed, created_at FROM todo WHERE user_id = ? ORDER BY priority, created_at DESC LIMIT 20",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, task, priority, completed, created_at FROM todo WHERE user_id = ? AND completed = 0 ORDER BY priority, created_at DESC LIMIT 20",
                (user_id,),
            ).fetchall()

        if not rows:
            label = "pending" if not show_completed else ""
            return {"response": f"Koi {label} tasks nahi hain! 'todo add [task]' se naya kaam add karo. 📋"}

        total = len(rows)
        done_count = sum(1 for r in rows if r["completed"])
        pending_count = total - done_count

        lines = [f"📋 Tumhare tasks ({pending_count} pending, {done_count} done):\n"]
        for row in rows:
            pemoji = self.PRIORITY_EMOJI.get(row["priority"], "🟡")
            status = "✅" if row["completed"] else "⬜"
            plabel = self.PRIORITY_LABEL.get(row["priority"], "Medium")
            lines.append(f"{status} #{row['id']} {pemoji} [{plabel}] {row['task']}")
        lines.append("\nMark done: 'done #3' | Delete: 'todo delete #3'")
        return {"response": "\n".join(lines)}

    def _complete_task(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        id_match = re.search(r'#?(\d+)', message)
        if not id_match:
            return {"response": "Kaunsa task complete karna hai? ID batao! Jaise: 'done #3'"}

        task_id = int(id_match.group(1))
        row = conn.execute(
            "SELECT id, task, completed FROM todo WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        ).fetchone()
        if not row:
            return {"response": f"Task #{task_id} nahi mila! ID check karo. ❌"}
        if row["completed"]:
            return {"response": f"Task #{task_id} pehle se hi complete hai! ✅"}

        conn.execute(
            "UPDATE todo SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        conn.commit()

        pending = conn.execute(
            "SELECT COUNT(*) as c FROM todo WHERE user_id = ? AND completed = 0", (user_id,)
        ).fetchone()["c"]

        return {"response": f"✅ '{row['task']}' - Done! ({pending} tasks baaki hain)"}

    def _delete_task(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        id_match = re.search(r'#?(\d+)', message)
        if not id_match:
            return {"response": "Kaunsa task delete karna hai? ID batao! Jaise: 'todo delete #3'"}

        task_id = int(id_match.group(1))
        row = conn.execute(
            "SELECT id, task FROM todo WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        ).fetchone()
        if not row:
            return {"response": f"Task #{task_id} nahi mila! ID check karo. ❌"}

        conn.execute("DELETE FROM todo WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()
        return {"response": f"🗑 Task #{task_id} '{row['task']}' delete ho gaya!"}
