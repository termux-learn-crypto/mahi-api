import json
from datetime import datetime
from collections import defaultdict
from .database import get_db


class KnowledgeGraph:
    def __init__(self):
        self._init_tables()

    def _init_tables(self):
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kg_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                source_id INTEGER,
                target_id INTEGER,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES kg_entities(id),
                FOREIGN KEY (target_id) REFERENCES kg_entities(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kg_entities_user
            ON kg_entities(user_id, name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_kg_relations_user
            ON kg_relations(user_id, source_id)
        """)
        conn.commit()
        conn.close()

    def add_entity(self, user_id: str, name: str, entity_type: str,
                   properties: dict = None) -> int:
        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM kg_entities WHERE user_id=? AND name=? AND entity_type=?",
            (user_id, name.lower(), entity_type)
        ).fetchone()

        if existing:
            entity_id = existing["id"]
            if properties:
                props = json.loads(conn.execute(
                    "SELECT properties FROM kg_entities WHERE id=?", (entity_id,)
                ).fetchone()["properties"] or "{}")
                props.update(properties)
                conn.execute(
                    "UPDATE kg_entities SET properties=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (json.dumps(props), entity_id)
                )
            conn.commit()
            conn.close()
            return entity_id

        cursor = conn.execute(
            "INSERT INTO kg_entities (user_id, name, entity_type, properties) VALUES (?, ?, ?, ?)",
            (user_id, name.lower(), entity_type, json.dumps(properties or {}))
        )
        entity_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return entity_id

    def add_relation(self, user_id: str, source_name: str, target_name: str,
                     relation_type: str, source_type: str = "person",
                     target_type: str = "person", weight: float = 1.0,
                     properties: dict = None) -> dict:
        source_id = self.add_entity(user_id, source_name, source_type)
        target_id = self.add_entity(user_id, target_name, target_type)

        conn = get_db()
        existing = conn.execute(
            "SELECT id, weight FROM kg_relations WHERE user_id=? AND source_id=? AND target_id=? AND relation_type=?",
            (user_id, source_id, target_id, relation_type)
        ).fetchone()

        if existing:
            new_weight = min(10.0, existing["weight"] + 0.1)
            conn.execute(
                "UPDATE kg_relations SET weight=?, properties=? WHERE id=?",
                (new_weight, json.dumps(properties or {}), existing["id"])
            )
            conn.commit()
            conn.close()
            return {"source": source_name, "target": target_name,
                    "relation": relation_type, "weight": new_weight, "updated": True}

        cursor = conn.execute(
            "INSERT INTO kg_relations (user_id, source_id, target_id, relation_type, weight, properties) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, source_id, target_id, relation_type, weight, json.dumps(properties or {}))
        )
        conn.commit()
        conn.close()
        return {"source": source_name, "target": target_name,
                "relation": relation_type, "weight": weight, "created": True}

    def get_entity(self, user_id: str, name: str) -> dict | None:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM kg_entities WHERE user_id=? AND name=?",
            (user_id, name.lower())
        ).fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "type": row["entity_type"],
            "properties": json.loads(row["properties"] or "{}"),
            "created_at": row["created_at"],
        }

    def get_relations(self, user_id: str, entity_name: str = None,
                      relation_type: str = None) -> list[dict]:
        conn = get_db()

        if entity_name:
            entity = self.get_entity(user_id, entity_name)
            if not entity:
                conn.close()
                return []

            rows = conn.execute("""
                SELECT r.*, s.name as source_name, s.entity_type as source_type,
                       t.name as target_name, t.entity_type as target_type
                FROM kg_relations r
                JOIN kg_entities s ON r.source_id = s.id
                JOIN kg_relations r2 ON r2.id = r.id
                JOIN kg_entities t ON r.target_id = t.id
                WHERE r.user_id = ? AND (r.source_id = ? OR r.target_id = ?)
            """, (user_id, entity["id"], entity["id"])).fetchall()
        elif relation_type:
            rows = conn.execute("""
                SELECT r.*, s.name as source_name, s.entity_type as source_type,
                       t.name as target_name, t.entity_type as target_type
                FROM kg_relations r
                JOIN kg_entities s ON r.source_id = s.id
                JOIN kg_entities t ON r.target_id = t.id
                WHERE r.user_id = ? AND r.relation_type = ?
            """, (user_id, relation_type)).fetchall()
        else:
            rows = conn.execute("""
                SELECT r.*, s.name as source_name, s.entity_type as source_type,
                       t.name as target_name, t.entity_type as target_type
                FROM kg_relations r
                JOIN kg_entities s ON r.source_id = s.id
                JOIN kg_entities t ON r.target_id = t.id
                WHERE r.user_id = ?
                ORDER BY r.weight DESC
                LIMIT 100
            """, (user_id,)).fetchall()

        conn.close()
        return [
            {
                "source": r["source_name"],
                "source_type": r["source_type"],
                "target": r["target_name"],
                "target_type": r["target_type"],
                "relation": r["relation_type"],
                "weight": r["weight"],
                "properties": json.loads(r["properties"] or "{}"),
            }
            for r in rows
        ]

    def get_connected(self, user_id: str, entity_name: str) -> dict:
        entity = self.get_entity(user_id, entity_name)
        if not entity:
            return {"entity": None, "connections": []}

        relations = self.get_relations(user_id, entity_name)

        connections = []
        for r in relations:
            if r["source"].lower() != entity_name.lower():
                connections.append({
                    "name": r["source"],
                    "type": r["source_type"],
                    "relation": r["relation"],
                    "direction": "incoming",
                    "weight": r["weight"],
                })
            if r["target"].lower() != entity_name.lower():
                connections.append({
                    "name": r["target"],
                    "type": r["target_type"],
                    "relation": r["relation"],
                    "direction": "outgoing",
                    "weight": r["weight"],
                })

        connections.sort(key=lambda x: x["weight"], reverse=True)

        return {"entity": entity, "connections": connections}

    def extract_from_text(self, user_id: str, text: str) -> dict:
        from .entities import entity_extractor

        entities = entity_extractor.extract(text)
        added = {"entities": [], "relations": []}

        names = entities.get("names", [])
        places = entities.get("places", [])

        for name in names:
            eid = self.add_entity(user_id, name, "person")
            added["entities"].append({"name": name, "type": "person", "id": eid})

        for place in places:
            eid = self.add_entity(user_id, place, "place")
            added["entities"].append({"name": place, "type": "place", "id": eid})

        if names and places:
            for name in names:
                for place in places:
                    rel = self.add_relation(user_id, name, place, "lives_in",
                                           "person", "place")
                    added["relations"].append(rel)

        if names and len(names) > 1:
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    rel = self.add_relation(user_id, names[i], names[j], "knows",
                                           "person", "person")
                    added["relations"].append(rel)

        return added

    def get_stats(self, user_id: str) -> dict:
        conn = get_db()
        entity_count = conn.execute(
            "SELECT COUNT(*) as c FROM kg_entities WHERE user_id=?", (user_id,)
        ).fetchone()["c"]

        relation_count = conn.execute(
            "SELECT COUNT(*) as c FROM kg_relations WHERE user_id=?", (user_id,)
        ).fetchone()["c"]

        type_dist = conn.execute("""
            SELECT entity_type, COUNT(*) as count
            FROM kg_entities WHERE user_id=?
            GROUP BY entity_type
        """, (user_id,)).fetchall()

        rel_dist = conn.execute("""
            SELECT relation_type, COUNT(*) as count, AVG(weight) as avg_weight
            FROM kg_relations WHERE user_id=?
            GROUP BY relation_type
        """, (user_id,)).fetchall()

        conn.close()

        return {
            "total_entities": entity_count,
            "total_relations": relation_count,
            "entity_types": {r["entity_type"]: r["count"] for r in type_dist},
            "relation_types": {
                r["relation_type"]: {"count": r["count"], "avg_weight": round(r["avg_weight"], 2)}
                for r in rel_dist
            },
        }

    def search(self, user_id: str, query: str) -> list[dict]:
        conn = get_db()
        rows = conn.execute("""
            SELECT * FROM kg_entities
            WHERE user_id=? AND name LIKE ?
            LIMIT 20
        """, (user_id, f"%{query.lower()}%")).fetchall()
        conn.close()

        results = []
        for row in rows:
            connected = self.get_connected(user_id, row["name"])
            results.append({
                "name": row["name"],
                "type": row["entity_type"],
                "properties": json.loads(row["properties"] or "{}"),
                "connections": connected["connections"][:5],
            })

        return results

    def clear(self, user_id: str):
        conn = get_db()
        conn.execute("DELETE FROM kg_relations WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM kg_entities WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()


knowledge_graph = KnowledgeGraph()
