from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship


class Graph:
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._adj_out: Dict[str, List[str]] = defaultdict(list)
        self._adj_in: Dict[str, List[str]] = defaultdict(list)

    @property
    def nodes(self) -> List[Node]:
        return list(self._nodes.values())

    @property
    def relationships(self) -> List[Relationship]:
        return list(self._relationships.values())

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def relationship_count(self) -> int:
        return len(self._relationships)

    def add_node(self, node: Node) -> Node:
        self._nodes[node.id] = node
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False
        rel_ids = list(self._adj_out[node_id]) + list(self._adj_in[node_id])
        for rid in rel_ids:
            self._remove_relationship_internal(rid)
        self._adj_out.pop(node_id, None)
        self._adj_in.pop(node_id, None)
        del self._nodes[node_id]
        return True

    def add_relationship(self, rel: Relationship) -> Relationship:
        if rel.source_id not in self._nodes:
            raise ValueError(f"Source node {rel.source_id!r} not found")
        if rel.target_id not in self._nodes:
            raise ValueError(f"Target node {rel.target_id!r} not found")
        self._relationships[rel.id] = rel
        self._adj_out[rel.source_id].append(rel.id)
        self._adj_in[rel.target_id].append(rel.id)
        return rel

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        return self._relationships.get(rel_id)

    def remove_relationship(self, rel_id: str) -> bool:
        return self._remove_relationship_internal(rel_id)

    def _remove_relationship_internal(self, rel_id: str) -> bool:
        rel = self._relationships.pop(rel_id, None)
        if rel is None:
            return False
        self._remove_adj(self._adj_out, rel.source_id, rel_id)
        self._remove_adj(self._adj_in, rel.target_id, rel_id)
        return True

    @staticmethod
    def _remove_adj(adj: Dict[str, List[str]], key: str, rel_id: str) -> None:
        if key in adj:
            try:
                adj[key].remove(rel_id)
            except ValueError:
                pass

    def get_node_relationships(
        self, node_id: str, direction: str = "both"
    ) -> List[Relationship]:
        rel_ids: Set[str] = set()
        if direction in ("out", "both"):
            rel_ids.update(self._adj_out.get(node_id, []))
        if direction in ("in", "both"):
            rel_ids.update(self._adj_in.get(node_id, []))
        return [self._relationships[rid] for rid in rel_ids if rid in self._relationships]

    def get_neighbors(
        self, node_id: str, direction: str = "both"
    ) -> List[Node]:
        rels = self.get_node_relationships(node_id, direction)
        neighbor_ids: Set[str] = set()
        for rel in rels:
            if direction in ("out", "both") and rel.source_id == node_id:
                neighbor_ids.add(rel.target_id)
            if direction in ("in", "both") and rel.target_id == node_id:
                neighbor_ids.add(rel.source_id)
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def find_nodes_by_type(self, type: str) -> List[Node]:
        return [n for n in self._nodes.values() if n.type == type]

    def find_nodes_by_property(self, key: str, value: Any) -> List[Node]:
        return [
            n for n in self._nodes.values()
            if n.properties.get(key) == value
        ]

    def find_relationships_by_type(self, type: str) -> List[Relationship]:
        return [r for r in self._relationships.values() if r.type == type]

    def find_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 10,
    ) -> Optional[List[Node]]:
        if from_id not in self._nodes or to_id not in self._nodes:
            return None
        visited: Set[str] = set()
        parent: Dict[str, Optional[str]] = {from_id: None}
        queue = [from_id]
        visited.add(from_id)
        while queue:
            current = queue.pop(0)
            if current == to_id:
                return self._reconstruct_path(parent, to_id)
            if len(self._reconstruct_path(parent, current)) > max_depth:
                continue
            for neighbor in self.get_neighbors(current, "out"):
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    parent[neighbor.id] = current
                    queue.append(neighbor.id)
        return None

    def _reconstruct_path(
        self, parent: Dict[str, Optional[str]], end_id: str
    ) -> List[Node]:
        path: List[Node] = []
        current: Optional[str] = end_id
        while current is not None:
            node = self._nodes.get(current)
            if node:
                path.insert(0, node)
            current = parent.get(current)
        return path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "relationships": [r.to_dict() for r in self._relationships.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Graph:
        g = cls()
        for nd in data.get("nodes", []):
            g.add_node(Node.from_dict(nd))
        for rd in data.get("relationships", []):
            g.add_relationship(Relationship.from_dict(rd))
        return g

    def clear(self) -> None:
        self._nodes.clear()
        self._relationships.clear()
        self._adj_out.clear()
        self._adj_in.clear()
