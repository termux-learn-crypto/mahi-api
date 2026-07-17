import time
import threading
from datetime import datetime


class BargeInManager:
    def __init__(self):
        self.active_sessions = {}
        self.lock = threading.Lock()

    def start_response(self, user_id: str, response_id: str, total_chunks: int = 1):
        with self.lock:
            self.active_sessions[user_id] = {
                "response_id": response_id,
                "started_at": time.time(),
                "chunks_sent": 0,
                "total_chunks": total_chunks,
                "cancelled": False,
                "interrupted_at": None,
            }

    def update_progress(self, user_id: str, chunks_sent: int):
        with self.lock:
            if user_id in self.active_sessions:
                self.active_sessions[user_id]["chunks_sent"] = chunks_sent

    def interrupt(self, user_id: str) -> dict:
        with self.lock:
            if user_id not in self.active_sessions:
                return {"status": "no_active_response"}

            session = self.active_sessions[user_id]
            if session["cancelled"]:
                return {"status": "already_cancelled"}

            session["cancelled"] = True
            session["interrupted_at"] = time.time()

            duration = session["interrupted_at"] - session["started_at"]
            chunks_played = session["chunks_sent"]

            return {
                "status": "interrupted",
                "response_id": session["response_id"],
                "duration": round(duration, 3),
                "chunks_played": chunks_played,
                "total_chunks": session["total_chunks"],
                "playback_percentage": round(
                    chunks_played / max(session["total_chunks"], 1) * 100, 1
                ),
            }

    def is_cancelled(self, user_id: str) -> bool:
        with self.lock:
            if user_id in self.active_sessions:
                return self.active_sessions[user_id]["cancelled"]
            return False

    def end_response(self, user_id: str):
        with self.lock:
            if user_id in self.active_sessions:
                session = self.active_sessions[user_id]
                session["completed_at"] = time.time()

    def cleanup(self, user_id: str):
        with self.lock:
            self.active_sessions.pop(user_id, None)

    def get_status(self, user_id: str) -> dict:
        with self.lock:
            if user_id in self.active_sessions:
                session = self.active_sessions[user_id]
                return {
                    "active": not session["cancelled"],
                    "response_id": session["response_id"],
                    "chunks_sent": session["chunks_sent"],
                    "total_chunks": session["total_chunks"],
                    "elapsed": round(time.time() - session["started_at"], 3),
                }
            return {"active": False}

    def get_all_active(self) -> dict:
        with self.lock:
            return {
                uid: {
                    "response_id": s["response_id"],
                    "chunks_sent": s["chunks_sent"],
                    "cancelled": s["cancelled"],
                }
                for uid, s in self.active_sessions.items()
            }
