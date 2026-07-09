from __future__ import annotations
from typing import Any, Dict, List, Optional

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.query.parser import parse_query, QueryParseError
from arcaniskg.query.traverser import GraphTraverser


class QueryExecutionError(Exception):
    pass


class QueryExecutor:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.traverser = GraphTraverser(graph)

    def execute(self, query_text: str) -> Dict[str, Any]:
        try:
            parsed = parse_query(query_text)
        except QueryParseError as e:
            raise QueryExecutionError(str(e))
        command = parsed.get("command", "raw")
        handler_name = command.replace(".", "_")
        handler = getattr(self, f"_execute_{handler_name}", None)
        if handler is None:
            raise QueryExecutionError(f"Unknown command: {command}")
        return handler(parsed)

    def execute_raw(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        nodes = []
        for n in self.graph.nodes:
            if parsed.get("source_type") and n.type != parsed["source_type"]:
                continue
            if parsed.get("target_type") and n.type != parsed["target_type"]:
                continue
            nodes.append(n.to_dict())
        rels = [r.to_dict() for r in self.graph.relationships]
        return {"nodes": nodes, "relationships": rels}

    def _execute_match(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        source_type = parsed.get("source_type")
        target_type = parsed.get("target_type")
        where = parsed.get("where")
        result_nodes: List[Node] = []
        result_rels: List[Relationship] = []
        for rel in self.graph.relationships:
            source = self.graph.get_node(rel.source_id)
            target = self.graph.get_node(rel.target_id)
            if source is None or target is None:
                continue
            if source_type and source.type != source_type:
                continue
            if target_type and target.type != target_type:
                continue
            if where:
                if not self._evaluate_where(source, target, rel, where):
                    continue
            result_nodes.append(source)
            result_nodes.append(target)
            result_rels.append(rel)
        seen_ids: set = set()
        unique_nodes = []
        for n in result_nodes:
            if n.id not in seen_ids:
                seen_ids.add(n.id)
                unique_nodes.append(n)
        return {
            "nodes": [n.to_dict() for n in unique_nodes],
            "relationships": [r.to_dict() for r in result_rels],
        }

    def _evaluate_where(
        self, source: Node, target: Node, rel: Relationship, condition: str
    ) -> bool:
        for node, prefix in [(source, "source."), (target, "target."), (None, "rel.")]:
            pass
        cond = condition.strip()
        eq_match = __import__("re").match(r"(\w+(?:\.\w+)?)\s*=\s*(.+)", cond)
        if eq_match:
            field_path = eq_match.group(1)
            expected = eq_match.group(2).strip().strip("\"'")
            parts = field_path.split(".")
            if parts[0] == "source":
                val = source.properties.get(parts[1]) if len(parts) > 1 else None
            elif parts[0] == "target":
                val = target.properties.get(parts[1]) if len(parts) > 1 else None
            elif parts[0] == "rel":
                val = rel.properties.get(parts[1]) if len(parts) > 1 else None
            else:
                val = None
            return str(val) == expected
        return True

    def _execute_traverse(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        start_id = parsed["start_id"]
        algorithm = parsed.get("algorithm", "bfs")
        max_depth = parsed.get("max_depth", 5)
        if algorithm == "dfs":
            result = self.traverser.dfs(start_id, max_depth=max_depth)
        else:
            result = self.traverser.bfs(start_id, max_depth=max_depth)
        return result.to_dict()

    def _execute_find(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        target = parsed.get("target", "nodes")
        by = parsed.get("by", "type")
        value = parsed.get("value", "")
        if target == "nodes":
            if by == "type":
                nodes = self.graph.find_nodes_by_type(value)
            else:
                kv = value.split("=", 1)
                key = kv[0].strip() if len(kv) > 0 else ""
                val = kv[1].strip().strip("\"'") if len(kv) > 1 else ""
                nodes = self.graph.find_nodes_by_property(key, val)
            return {"nodes": [n.to_dict() for n in nodes]}
        else:
            if by == "type":
                rels = self.graph.find_relationships_by_type(value)
            else:
                kv = value.split("=", 1)
                key = kv[0].strip()
                val = kv[1].strip().strip("\"'") if len(kv) > 1 else ""
                rels = [
                    r for r in self.graph.relationships
                    if r.properties.get(key) == val
                ]
            return {"relationships": [r.to_dict() for r in rels]}

    def _execute_node_get(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        node = self.graph.get_node(parsed["node_id"])
        if node is None:
            raise QueryExecutionError(f"Node not found: {parsed['node_id']}")
        return {"node": node.to_dict()}

    def _execute_rel_get(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        rel = self.graph.get_relationship(parsed["rel_id"])
        if rel is None:
            raise QueryExecutionError(f"Relationship not found: {parsed['rel_id']}")
        return {"relationship": rel.to_dict()}

    def _execute_path(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        path = self.traverser.find_shortest_path(
            parsed["from_id"], parsed["to_id"]
        )
        if path is None:
            return {"path": [], "found": False}
        return {"path": [n.to_dict() for n in path], "found": True}
