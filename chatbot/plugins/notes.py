import re
from datetime import datetime
from . import Plugin
from ..database import get_db


class NotesPlugin(Plugin):
    def __init__(self):
        super().__init__(
            name="notes",
            description="Notes system - create, read, update, delete, list, search your notes",
            version="1.0.0",
        )
        self.commands = ["note", "notes", "yaad", "save", "likh", "khalo"]
        self.keywords = [
            "note", "notes", "yaad", "save", "likh", "khalo", "likhna",
            "dusra", "hatao", "search", "dhoondo", "list", "sab notes",
        ]

    def can_handle(self, intent: str, message: str) -> bool:
        if intent == "notes":
            return True
        msg = message.lower()
        patterns = [
            r'\b(note|notes|yaad|save|likh|khalo|likhna|search|dhoondo|list|sab)\b',
        ]
        return any(re.search(p, msg) for p in patterns)

    def execute(self, user_id: str, message: str, context: dict) -> dict:
        msg = message.strip()
        conn = get_db()

        try:
            if re.search(r'\b(sab notes|list notes|saare notes|notes dikhao|show notes|meri notes)\b', msg, re.I):
                return self._list_notes(conn, user_id)
            if re.search(r'\b(search|dhoondo|khojo)\b', msg, re.I):
                return self._search_notes(conn, user_id, msg)
            if re.search(r'\b(hatao|delete|remove|khalo|mita)\b', msg, re.I):
                return self._delete_note(conn, user_id, msg)
            if re.search(r'\b(update|edit|badlo|sudhar|change)\b', msg, re.I):
                return self._update_note(conn, user_id, msg)
            return self._create_note(conn, user_id, msg)
        finally:
            conn.close()

    def _init_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def _create_note(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        content = re.sub(
            r'\b(note|notes|yaad|save|likh|khalo|likhna|pe|par|mein|karo|ye|wo|do|aap|tum|main|i want|i need to|i have to|i should)\b',
            '', message, flags=re.I
        ).strip()
        content = content.strip('".!?,')
        if not content:
            return {"response": "Kya yaad karna hai? Batao content! 📝"}

        lines = content.split('\n', 1)
        title = lines[0][:60] if len(lines) > 1 else content[:60]
        body = lines[1].strip() if len(lines) > 1 else content

        cursor = conn.execute(
            "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, body),
        )
        conn.commit()
        note_id = cursor.lastrowid
        return {
            "response": f"📝 Note save ho gaya! (ID: {note_id})\n\nTitle: {title}\nContent: {body[:200]}",
            "data": {"note_id": note_id, "title": title, "content": body},
        }

    def _list_notes(self, conn, user_id: str) -> dict:
        self._init_table(conn)
        rows = conn.execute(
            "SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC LIMIT 20",
            (user_id,),
        ).fetchall()

        if not rows:
            return {"response": "Tumhare paas koi notes nahi abhi! 'save karo [content]' se note banao. 📝"}

        lines = [f"📋 Tumhare {len(rows)} notes:\n"]
        for row in rows:
            ts = row["created_at"][:16] if row["created_at"] else ""
            title = (row["title"] or "Bina title")[:40]
            content_preview = (row["content"] or "")[:50]
            lines.append(f"#{row['id']} | {title}")
            lines.append(f"   📅 {ts} | {content_preview}...")
            lines.append("")
        lines.append("Detail dekho: 'note #3' | Delete: 'note hatao #3'")
        return {"response": "\n".join(lines)}

    def _search_notes(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        query = re.sub(
            r'\b(search|dhoondo|khojo|notes|note|mein|se|ko)\b', '', message, flags=re.I
        ).strip()
        if not query:
            return {"response": "Kya dhoondna hai notes mein? Keyword batao! 🔍"}

        rows = conn.execute(
            "SELECT id, title, content, created_at FROM notes WHERE user_id = ? AND (title LIKE ? OR content LIKE ?) ORDER BY updated_at DESC LIMIT 10",
            (user_id, f"%{query}%", f"%{query}%"),
        ).fetchall()

        if not rows:
            return {"response": f"'{query}' se koi note nahi mila! 🔍"}

        lines = [f"🔍 '{query}' se {len(rows)} notes mile:\n"]
        for row in rows:
            title = (row["title"] or "Bina title")[:40]
            content_preview = (row["content"] or "")[:60]
            lines.append(f"#{row['id']} | {title}")
            lines.append(f"   {content_preview}...\n")
        return {"response": "\n".join(lines)}

    def _delete_note(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        id_match = re.search(r'#?(\d+)', message)
        if not id_match:
            return {"response": "Kaunsa note delete karna hai? ID batao! Jaise: 'note hatao #3'"}

        note_id = int(id_match.group(1))
        row = conn.execute(
            "SELECT id, title FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        ).fetchone()
        if not row:
            return {"response": f"Note #{note_id} nahi mila! ID check karo. ❌"}

        conn.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        conn.commit()
        return {"response": f"🗑 Note #{note_id} '{row['title']}' delete ho gaya!"}

    def _update_note(self, conn, user_id: str, message: str) -> dict:
        self._init_table(conn)
        id_match = re.search(r'#?(\d+)', message)
        new_content = re.sub(
            r'\b(update|edit|badlo|sudhar|change|note|notes|#?\d+)\b', '', message, flags=re.I
        ).strip()

        if not id_match:
            return {"response": "Kaunsa note update karna hai? ID aur naya content batao! ✏\uFE0F\nExample: 'edit #3 naya content'"}
        if not new_content:
            return {"response": "Naya content kya hai? Batao! ✏\uFE0F"}

        note_id = int(id_match.group(1))
        row = conn.execute(
            "SELECT id, title FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        ).fetchone()
        if not row:
            return {"response": f"Note #{note_id} nahi mila! ID check karo. ❌"}

        conn.execute(
            "UPDATE notes SET content = ?, title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (new_content, new_content[:60], note_id, user_id),
        )
        conn.commit()
        return {"response": f"✏\uFE0F Note #{note_id} update ho gaya!\nNaya content: {new_content[:200]}"}
