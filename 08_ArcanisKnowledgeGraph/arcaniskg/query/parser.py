from __future__ import annotations
import re
from typing import Any, Dict, List, Optional


class QueryParseError(Exception):
    pass


def parse_query(text: str) -> Dict[str, Any]:
    text = text.strip()
    if not text:
        raise QueryParseError("Empty query")
    upper = text.upper()
    if upper.startswith("MATCH "):
        return _parse_match(text)
    elif upper.startswith("TRAVERSE "):
        return _parse_traverse(text)
    elif upper.startswith("FIND "):
        return _parse_find(text)
    elif upper.startswith("NODE.GET "):
        return _parse_node_get(text)
    elif upper.startswith("REL.GET "):
        return _parse_rel_get(text)
    elif upper.startswith("PATH "):
        return _parse_path(text)
    else:
        return {"command": "raw", "query": text}


def _parse_match(text: str) -> Dict[str, Any]:
    pattern = r"MATCH\s+\((\w+)(?::(\w+))?\)\s*(?:-\[(?:\w+)?(?::(\w+))?\]->\s*\((\w+)(?::(\w+))?\))?"
    m = re.match(pattern, text, re.IGNORECASE)
    if not m:
        return {"command": "match", "raw": text}
    result: Dict[str, Any] = {"command": "match"}
    groups = m.groups()
    result["source_alias"] = groups[0]
    if groups[1]:
        result["source_type"] = groups[1]
    if groups[2]:
        result["rel_type"] = groups[2]
    if groups[3]:
        result["target_alias"] = groups[3]
    if groups[4]:
        result["target_type"] = groups[4]
    where_pos = text.upper().find(" WHERE ")
    if where_pos >= 0:
        result["where"] = text[where_pos + 7 :].strip()
    return result


def _parse_traverse(text: str) -> Dict[str, Any]:
    pattern = r"TRAVERSE\s+(\S+)\s+(BFS|DFS)\s+DEPTH\s+(\d+)"
    m = re.match(pattern, text, re.IGNORECASE)
    if not m:
        return {"command": "traverse", "raw": text}
    return {
        "command": "traverse",
        "start_id": m.group(1),
        "algorithm": m.group(2).lower(),
        "max_depth": int(m.group(3)),
    }


def _parse_find(text: str) -> Dict[str, Any]:
    pattern = r"FIND\s+(NODES|RELS?)\s+(?:BY\s+(TYPE|PROPERTY))\s+(.+)"
    m = re.match(pattern, text, re.IGNORECASE)
    if not m:
        return {"command": "find", "raw": text}
    target = m.group(1).upper()
    by = m.group(2).upper()
    value = m.group(3).strip()
    return {
        "command": "find",
        "target": "relationships" if target in ("REL", "RELS") else "nodes",
        "by": by.lower(),
        "value": value,
    }


def _parse_node_get(text: str) -> Dict[str, Any]:
    pattern = r"NODE\.GET\s+(\S+)"
    m = re.match(pattern, text, re.IGNORECASE)
    if not m:
        return {"command": "node.get", "raw": text}
    return {"command": "node.get", "node_id": m.group(1)}


def _parse_rel_get(text: str) -> Dict[str, Any]:
    pattern = r"REL\.GET\s+(\S+)"
    m = re.match(pattern, text, re.IGNORECASE)
    if not m:
        return {"command": "rel.get", "raw": text}
    return {"command": "rel.get", "rel_id": m.group(1)}


def _parse_path(text: str) -> Dict[str, Any]:
    pattern = r"PATH\s+(\S+)\s+TO\s+(\S+)(?:\s+DEPTH\s+(\d+))?"
    m = re.match(pattern, text, re.IGNORECASE)
    if not m:
        return {"command": "path", "raw": text}
    return {
        "command": "path",
        "from_id": m.group(1),
        "to_id": m.group(2),
        "max_depth": int(m.group(3)) if m.group(3) else 10,
    }
