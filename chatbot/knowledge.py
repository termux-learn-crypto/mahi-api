import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from .config import config
from .database import get_db


class KnowledgeSystem:
    def __init__(self):
        self._init_tables()
        self.chunks = {}

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                chunk_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_user ON document_chunks(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_content ON document_chunks(content)")
        conn.commit()
        conn.close()

    def add_document(self, user_id: str, file_path: str, filename: str) -> dict:
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in config.ALLOWED_EXTENSIONS:
            return {"error": f"Unsupported file type: {ext}"}

        content = self._extract_content(file_path, ext)
        if not content:
            return {"error": "Could not extract content"}

        chunks = self._chunk_text(content)
        conn = get_db()
        cursor = conn.execute("""
            INSERT INTO documents (user_id, filename, file_type, file_size, chunk_count)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, filename, ext, os.path.getsize(file_path), len(chunks)))
        doc_id = cursor.lastrowid

        for i, chunk in enumerate(chunks):
            conn.execute("""
                INSERT INTO document_chunks (doc_id, user_id, chunk_index, content)
                VALUES (?, ?, ?, ?)
            """, (doc_id, user_id, i, chunk))
        conn.commit()
        conn.close()

        return {
            "doc_id": doc_id,
            "filename": filename,
            "chunks": len(chunks),
            "size": os.path.getsize(file_path),
        }

    def _extract_content(self, file_path: str, ext: str) -> str:
        try:
            if ext == "txt" or ext == "md":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            elif ext == "pdf":
                return self._extract_pdf(file_path)
            elif ext == "docx":
                return self._extract_docx(file_path)
            elif ext == "csv" or ext == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception:
            return ""
        return ""

    def _extract_pdf(self, file_path: str) -> str:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception:
            return ""

    def _extract_docx(self, file_path: str) -> str:
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except Exception:
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def search(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT dc.id, dc.content, dc.doc_id, d.filename,
                   dc.chunk_index, d.file_type
            FROM document_chunks dc
            JOIN documents d ON dc.doc_id = d.id
            WHERE dc.user_id = ? AND dc.content LIKE ?
            ORDER BY dc.id DESC
            LIMIT ?
        """, (user_id, f"%{query}%", limit)).fetchall()
        conn.close()

        results = []
        for row in rows:
            score = self._calculate_relevance(query, row["content"])
            if score > 0.1:
                results.append({
                    "content": row["content"],
                    "filename": row["filename"],
                    "chunk_index": row["chunk_index"],
                    "relevance": round(score, 3),
                })
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]

    def _calculate_relevance(self, query: str, text: str) -> float:
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        if not query_words:
            return 0.0
        intersection = query_words & text_words
        return len(intersection) / len(query_words)

    def list_documents(self, user_id: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, filename, file_type, file_size, chunk_count, created_at
            FROM documents WHERE user_id=?
            ORDER BY created_at DESC
        """, (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def delete_document(self, doc_id: int, user_id: str) -> bool:
        conn = get_db()
        conn.execute("DELETE FROM document_chunks WHERE doc_id=? AND user_id=?", (doc_id, user_id))
        cursor = conn.execute("DELETE FROM documents WHERE id=? AND user_id=?", (doc_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def get_stats(self, user_id: str) -> dict:
        conn = get_db()
        doc_count = conn.execute(
            "SELECT COUNT(*) as c FROM documents WHERE user_id=?", (user_id,)
        ).fetchone()["c"]
        chunk_count = conn.execute(
            "SELECT COUNT(*) as c FROM document_chunks WHERE user_id=?", (user_id,)
        ).fetchone()["c"]
        conn.close()
        return {"documents": doc_count, "total_chunks": chunk_count}
