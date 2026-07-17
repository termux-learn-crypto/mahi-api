import json
import random
from datetime import datetime, timedelta
from collections import defaultdict
from .database import get_db


class ABTesting:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                variants TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER,
                user_id TEXT NOT NULL,
                variant TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES ab_tests(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ab_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER,
                user_id TEXT NOT NULL,
                variant TEXT NOT NULL,
                metric TEXT NOT NULL,
                value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES ab_tests(id)
            )
        """)
        conn.commit()
        conn.close()

    def create_test(self, test_name: str, variants: list[str],
                    weights: list[float] = None) -> int:
        if not weights:
            weights = [1.0 / len(variants)] * len(variants)

        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO ab_tests (test_name, variants) VALUES (?, ?)",
            (test_name, json.dumps({"variants": variants, "weights": weights}))
        )
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return test_id

    def assign_variant(self, test_id: int, user_id: str) -> str:
        conn = get_db()

        existing = conn.execute(
            "SELECT variant FROM ab_assignments WHERE test_id=? AND user_id=?",
            (test_id, user_id)
        ).fetchone()

        if existing:
            conn.close()
            return existing["variant"]

        test = conn.execute(
            "SELECT variants FROM ab_tests WHERE id=?", (test_id,)
        ).fetchone()

        if not test:
            conn.close()
            return None

        config = json.loads(test["variants"])
        variants = config["variants"]
        weights = config["weights"]

        variant = random.choices(variants, weights=weights, k=1)[0]

        conn.execute(
            "INSERT INTO ab_assignments (test_id, user_id, variant) VALUES (?, ?, ?)",
            (test_id, user_id, variant)
        )
        conn.commit()
        conn.close()
        return variant

    def record_result(self, test_id: int, user_id: str, metric: str, value: float):
        conn = get_db()

        assignment = conn.execute(
            "SELECT variant FROM ab_assignments WHERE test_id=? AND user_id=?",
            (test_id, user_id)
        ).fetchone()

        if not assignment:
            conn.close()
            return

        variant = assignment["variant"]

        conn.execute(
            "INSERT INTO ab_results (test_id, user_id, variant, metric, value) VALUES (?, ?, ?, ?, ?)",
            (test_id, user_id, variant, metric, value)
        )
        conn.commit()
        conn.close()

    def get_results(self, test_id: int) -> dict:
        conn = get_db()

        test = conn.execute(
            "SELECT * FROM ab_tests WHERE id=?", (test_id,)
        ).fetchone()

        if not test:
            conn.close()
            return None

        config = json.loads(test["variants"])

        results = conn.execute("""
            SELECT variant, metric, AVG(value) as avg_value, COUNT(*) as count
            FROM ab_results WHERE test_id=?
            GROUP BY variant, metric
        """, (test_id,)).fetchall()

        variant_results = defaultdict(lambda: defaultdict(dict))
        for r in results:
            variant_results[r["variant"]][r["metric"]] = {
                "avg": round(r["avg_value"], 3),
                "count": r["count"],
            }

        total_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) as c FROM ab_assignments WHERE test_id=?",
            (test_id,)
        ).fetchone()["c"]

        conn.close()

        return {
            "test_id": test_id,
            "test_name": test["test_name"],
            "status": test["status"],
            "variants": config["variants"],
            "total_users": total_users,
            "results": dict(variant_results),
            "created_at": test["created_at"],
        }

    def end_test(self, test_id: int) -> dict:
        conn = get_db()
        conn.execute(
            "UPDATE ab_tests SET status='ended', ended_at=CURRENT_TIMESTAMP WHERE id=?",
            (test_id,)
        )
        conn.commit()
        conn.close()
        return self.get_results(test_id)

    def get_winner(self, test_id: int, metric: str) -> dict:
        results = self.get_results(test_id)
        if not results:
            return None

        variant_scores = {}
        for variant, metrics in results["results"].items():
            if metric in metrics:
                variant_scores[variant] = metrics[metric]["avg"]

        if not variant_scores:
            return None

        winner = max(variant_scores, key=variant_scores.get)
        return {
            "winner": winner,
            "score": variant_scores[winner],
            "all_scores": variant_scores,
        }

    def get_all_tests(self, status: str = None) -> list[dict]:
        conn = get_db()
        if status:
            rows = conn.execute(
                "SELECT * FROM ab_tests WHERE status=? ORDER BY created_at DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ab_tests ORDER BY created_at DESC"
            ).fetchall()
        conn.close()

        return [
            {
                "id": r["id"],
                "name": r["test_name"],
                "status": r["status"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]


ab_testing = ABTesting()
