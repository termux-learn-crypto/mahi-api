import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> dict:
        now = time.time()
        window_start = now - self.window_seconds

        self.requests[user_id] = [
            t for t in self.requests[user_id] if t > window_start
        ]

        current_count = len(self.requests[user_id])

        if current_count >= self.max_requests:
            oldest = self.requests[user_id][0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return {
                "allowed": False,
                "remaining": 0,
                "retry_after": retry_after,
                "reset_at": int(oldest + self.window_seconds),
            }

        self.requests[user_id].append(now)

        return {
            "allowed": True,
            "remaining": self.max_requests - current_count - 1,
            "retry_after": 0,
            "reset_at": int(now + self.window_seconds),
        }

    def get_usage(self, user_id: str) -> dict:
        now = time.time()
        window_start = now - self.window_seconds

        self.requests[user_id] = [
            t for t in self.requests[user_id] if t > window_start
        ]

        return {
            "user_id": user_id,
            "used": len(self.requests[user_id]),
            "limit": self.max_requests,
            "remaining": self.max_requests - len(self.requests[user_id]),
            "window_seconds": self.window_seconds,
        }

    def reset(self, user_id: str):
        self.requests[user_id] = []


limiter = RateLimiter(max_requests=30, window_seconds=60)
