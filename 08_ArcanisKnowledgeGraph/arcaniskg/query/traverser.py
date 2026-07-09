from __future__ import annotations
from typing import Callable, Dict, List, Optional, Set, Tuple
from collections import deque

from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.graph.graph import Graph


class TraversalResult:
    def __init__(
        self,
        nodes: Optional[List[Node]] = None,
        relationships: Optional[List[Relationship]] = None,
        path: Optional[List[Node]] = None,
    ):
        self.nodes = nodes or []
        self.relationships = relationships or []
        self.path = path or []

    def to_dict(self) -> Dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relationships": [r.to_dict() for r in self.relationships],
        }


class GraphTraverser:
    def __init__(self, graph: Graph):
        self.graph = graph

    def bfs(
        self,
        start_id: str,
        max_depth: int = 5,
        direction: str = "out",
        node_filter: Optional[Callable[[Node], bool]] = None,
    ) -> TraversalResult:
        if start_id not in self.graph._nodes:
            return TraversalResult()
        visited: Set[str] = set()
        result_nodes: List[Node] = []
        result_rels: List[Relationship] = []
        queue: deque[Tuple[str, int]] = deque()
        queue.append((start_id, 0))
        visited.add(start_id)
        while queue:
            current_id, depth = queue.popleft()
            if depth > 0:
                node = self.graph._nodes.get(current_id)
                if node and (node_filter is None or node_filter(node)):
                    result_nodes.append(node)
            if depth >= max_depth:
                continue
            for rel in self.graph.get_node_relationships(current_id, direction):
                neighbor_id = (
                    rel.target_id if rel.source_id == current_id else rel.source_id
                )
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    result_rels.append(rel)
                    queue.append((neighbor_id, depth + 1))
        return TraversalResult(nodes=result_nodes, relationships=result_rels)

    def dfs(
        self,
        start_id: str,
        max_depth: int = 10,
        direction: str = "out",
        node_filter: Optional[Callable[[Node], bool]] = None,
    ) -> TraversalResult:
        if start_id not in self.graph._nodes:
            return TraversalResult()
        visited: Set[str] = set()
        result_nodes: List[Node] = []
        result_rels: List[Relationship] = []
        stack: List[Tuple[str, int]] = [(start_id, 0)]
        while stack:
            current_id, depth = stack.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            if depth > 0:
                node = self.graph._nodes.get(current_id)
                if node and (node_filter is None or node_filter(node)):
                    result_nodes.append(node)
            if depth >= max_depth:
                continue
            for rel in self.graph.get_node_relationships(current_id, direction):
                neighbor_id = (
                    rel.target_id if rel.source_id == current_id else rel.source_id
                )
                if neighbor_id not in visited:
                    result_rels.append(rel)
                    stack.append((neighbor_id, depth + 1))
        return TraversalResult(nodes=result_nodes, relationships=result_rels)

    def find_shortest_path(
        self, from_id: str, to_id: str
    ) -> Optional[List[Node]]:
        return self.graph.find_path(from_id, to_id)

    def find_all_paths(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 6,
    ) -> List[List[Node]]:
        if from_id not in self.graph._nodes or to_id not in self.graph._nodes:
            return []
        paths: List[List[Node]] = []
        self._dfs_all_paths(from_id, to_id, {from_id}, [], paths, max_depth)
        return paths

    def _dfs_all_paths(
        self,
        current: str,
        target: str,
        visited: Set[str],
        current_path: List[Node],
        paths: List[List[Node]],
        max_depth: int,
    ) -> None:
        node = self.graph._nodes.get(current)
        if node is None:
            return
        current_path.append(node)
        if current == target:
            paths.append(list(current_path))
            current_path.pop()
            return
        if len(current_path) > max_depth:
            current_path.pop()
            return
        for rel in self.graph.get_node_relationships(current, "out"):
            neighbor_id = rel.target_id
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                self._dfs_all_paths(
                    neighbor_id, target, visited, current_path, paths, max_depth
                )
                visited.discard(neighbor_id)
        current_path.pop()

    def find_subgraph(
        self,
        node_ids: List[str],
        max_depth: int = 2,
    ) -> Graph:
        sub = Graph()
        for nid in node_ids:
            node = self.graph.get_node(nid)
            if node:
                sub.add_node(Node(id=node.id, type=node.type, properties=dict(node.properties)))
        frontier = set(node_ids)
        for _ in range(max_depth):
            next_frontier: Set[str] = set()
            for nid in frontier:
                for rel in self.graph.get_node_relationships(nid, "both"):
                    other_id = rel.target_id if rel.source_id == nid else rel.source_id
                    other_node = self.graph.get_node(other_id)
                    if other_node and sub.get_node(other_id) is None:
                        sub.add_node(
                            Node(id=other_node.id, type=other_node.type, properties=dict(other_node.properties))
                        )
                        next_frontier.add(other_id)
                    if sub.get_relationship(rel.id) is None:
                        sub.add_relationship(
                            Relationship(
                                source_id=rel.source_id,
                                target_id=rel.target_id,
                                type=rel.type,
                                id=rel.id,
                                properties=dict(rel.properties),
                            )
                        )
            frontier = next_frontier
        return sub
