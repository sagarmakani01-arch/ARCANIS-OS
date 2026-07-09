import re
import json
from typing import Dict, Any, Optional, Tuple


class ArcanisQLParser:
    def parse(self, query: str) -> Dict[str, Any]:
        query = query.strip()
        if not query:
            raise ValueError("Empty query")

        if query.upper().startswith("CREATE COLLECTION"):
            return self._parse_create_collection(query)
        elif query.upper().startswith("INSERT INTO"):
            return self._parse_insert(query)
        elif query.upper().startswith("SELECT"):
            return self._parse_select(query)
        elif query.upper().startswith("UPDATE"):
            return self._parse_update(query)
        elif query.upper().startswith("DELETE FROM"):
            return self._parse_delete(query)
        elif query.upper().startswith("KV.SET"):
            return self._parse_kv_set(query)
        elif query.upper().startswith("KV.GET"):
            return self._parse_kv_get(query)
        elif query.upper().startswith("KV.DEL"):
            return self._parse_kv_del(query)
        elif query.upper().startswith("VECTOR.INSERT"):
            return self._parse_vector_insert(query)
        elif query.upper().startswith("VECTOR.SEARCH"):
            return self._parse_vector_search(query)
        elif query.upper().startswith("EMBED.STORE"):
            return self._parse_embed_store(query)
        elif query.upper().startswith("EMBED.SEARCH"):
            return self._parse_embed_search(query)
        elif query.upper().startswith("RETRIEVE"):
            return self._parse_retrieve(query)
        elif query.upper().startswith("CREATE INDEX"):
            return self._parse_create_index(query)
        elif query.upper().startswith("BACKUP TO"):
            return {"command": "backup", "path": query[len("BACKUP TO"):].strip().strip('"').strip("'")}
        elif query.upper().startswith("INFO"):
            return {"command": "info"}
        else:
            raise ValueError(f"Unknown command: {query.split()[0] if query.split() else ''}")

    def _parse_create_collection(self, query: str) -> Dict:
        pattern = r"CREATE\s+COLLECTION\s+(\w+)(?:\s+TYPE\s+(\w+))?"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid CREATE COLLECTION syntax")
        return {
            "command": "create_collection",
            "name": m.group(1),
            "type": (m.group(2) or "structured").lower(),
        }

    def _parse_insert(self, query: str) -> Dict:
        pattern = r"INSERT\s+INTO\s+(\w+)\s+(.*)"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid INSERT INTO syntax")
        collection = m.group(1)
        data = json.loads(m.group(2))
        return {"command": "insert", "collection": collection, "data": data}

    def _parse_select(self, query: str) -> Dict:
        pattern = r"SELECT\s+(\*|\w+(?:,\s*\w+)*)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+?))?(?:\s+LIMIT\s+(\d+))?(?:\s+OFFSET\s+(\d+))?$"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid SELECT syntax")
        result = {
            "command": "select",
            "fields": m.group(1),
            "collection": m.group(2),
            "limit": int(m.group(4)) if m.group(4) else 100,
            "offset": int(m.group(5)) if m.group(5) else 0,
        }
        if m.group(3):
            filters = {}
            for cond in m.group(3).split("AND"):
                cond = cond.strip()
                if "=" in cond:
                    k, v = cond.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    try:
                        v = json.loads(v)
                    except (json.JSONDecodeError, ValueError):
                        pass
                    filters[k] = v
            result["filters"] = filters
        return result

    def _parse_update(self, query: str) -> Dict:
        pattern = r"UPDATE\s+(\w+)\s+SET\s+(.*?)(?:\s+WHERE\s+id=(\d+))?$"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid UPDATE syntax")
        return {
            "command": "update",
            "collection": m.group(1),
            "data": json.loads(m.group(2)),
            "id": int(m.group(3)) if m.group(3) else None,
        }

    def _parse_delete(self, query: str) -> Dict:
        pattern = r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+id=(\d+))?$"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid DELETE FROM syntax")
        return {
            "command": "delete",
            "collection": m.group(1),
            "id": int(m.group(2)) if m.group(2) else None,
        }

    def _parse_kv_set(self, query: str) -> Dict:
        pattern = r"KV\.SET\s+(\w+)\s+(\S+)\s+(.*)"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid KV.SET syntax")
        value_str = m.group(3).strip()
        try:
            value = json.loads(value_str)
        except (json.JSONDecodeError, ValueError):
            value = value_str
        return {"command": "kv_set", "collection": m.group(1), "key": m.group(2), "value": value}

    def _parse_kv_get(self, query: str) -> Dict:
        pattern = r"KV\.GET\s+(\w+)\s+(\S+)"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid KV.GET syntax")
        return {"command": "kv_get", "collection": m.group(1), "key": m.group(2)}

    def _parse_kv_del(self, query: str) -> Dict:
        pattern = r"KV\.DEL\s+(\w+)\s+(\S+)"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid KV.DEL syntax")
        return {"command": "kv_del", "collection": m.group(1), "key": m.group(2)}

    def _parse_vector_insert(self, query: str) -> Dict:
        pattern = r"VECTOR\.INSERT\s+(\w+)\s+(\[.*?\])(?:\s+METADATA\s+(\{.*\}))?"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid VECTOR.INSERT syntax")
        result = {"command": "vector_insert", "collection": m.group(1), "vector": json.loads(m.group(2))}
        if m.group(3):
            result["metadata"] = json.loads(m.group(3))
        return result

    def _parse_vector_search(self, query: str) -> Dict:
        pattern = r"VECTOR\.SEARCH\s+(\w+)\s+(\[.*?\])(?:\s+TOP_K\s+(\d+))?(?:\s+METRIC\s+(\w+))?"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid VECTOR.SEARCH syntax")
        return {
            "command": "vector_search",
            "collection": m.group(1),
            "vector": json.loads(m.group(2)),
            "top_k": int(m.group(3)) if m.group(3) else 10,
            "metric": (m.group(4) or "cosine").lower(),
        }

    def _parse_embed_store(self, query: str) -> Dict:
        pattern = r"EMBED\.STORE\s+(\w+)\s+(\[.*?\])(?:\s+METADATA\s+(\{.*\}))?"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid EMBED.STORE syntax")
        result = {"command": "embed_store", "collection": m.group(1), "vector": json.loads(m.group(2))}
        if m.group(3):
            result["metadata"] = json.loads(m.group(3))
        return result

    def _parse_embed_search(self, query: str) -> Dict:
        result = self._parse_vector_search(query)
        result["command"] = "embed_search"
        return result

    def _parse_retrieve(self, query: str) -> Dict:
        pattern = r"RETRIEVE\s+(\w+)\s+(\[.*?\])(?:\s+TOP_K\s+(\d+))?(?:\s+MIN_SCORE\s+([\d.]+))?"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid RETRIEVE syntax")
        return {
            "command": "retrieve",
            "collection": m.group(1),
            "vector": json.loads(m.group(2)),
            "top_k": int(m.group(3)) if m.group(3) else 5,
            "min_score": float(m.group(4)) if m.group(4) else 0.0,
        }

    def _parse_create_index(self, query: str) -> Dict:
        pattern = r"CREATE\s+INDEX\s+ON\s+(\w+)\s+\((\w+)\)(?:\s+TYPE\s+(\w+))?"
        m = re.match(pattern, query, re.IGNORECASE)
        if not m:
            raise ValueError("Invalid CREATE INDEX syntax")
        return {
            "command": "create_index",
            "collection": m.group(1),
            "field": m.group(2),
            "type": (m.group(3) or "btree").lower(),
        }
