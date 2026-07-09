from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship


class SemanticAnalyzer:
    def __init__(self, graph: Graph):
        self.graph = graph

    def find_semantically_similar(
        self, node_id: str, max_results: int = 10
    ) -> List[Tuple[Node, float]]:
        node = self.graph.get_node(node_id)
        if node is None:
            return []
        scores: List[Tuple[Node, float]] = []
        for other in self.graph.nodes:
            if other.id == node_id:
                continue
            score = self._compute_semantic_similarity(node, other)
            scores.append((other, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:max_results]

    def _compute_semantic_similarity(self, a: Node, b: Node) -> float:
        type_score = 1.0 if a.type == b.type else 0.3
        shared_props = 0
        total_props = 0
        all_keys = set(a.properties.keys()) | set(b.properties.keys())
        for key in all_keys:
            va = a.properties.get(key)
            vb = b.properties.get(key)
            if va is not None and vb is not None:
                total_props += 1
                if va == vb:
                    shared_props += 1
        prop_score = shared_props / total_props if total_props > 0 else 0.5
        shared_neighbors = self._count_shared_neighbors(a.id, b.id)
        neighbor_score = min(shared_neighbors / 5.0, 1.0)
        return 0.4 * type_score + 0.4 * prop_score + 0.2 * neighbor_score

    def _count_shared_neighbors(self, id_a: str, id_b: str) -> int:
        neighbors_a = self._get_neighbor_set(id_a)
        neighbors_b = self._get_neighbor_set(id_b)
        return len(neighbors_a & neighbors_b)

    def _get_neighbor_set(self, node_id: str) -> Set[str]:
        neighbors: Set[str] = set()
        for rel in self.graph.get_node_relationships(node_id, "both"):
            if rel.source_id == node_id:
                neighbors.add(rel.target_id)
            else:
                neighbors.add(rel.source_id)
        return neighbors

    def infer_node_type(self, properties: Dict[str, Any]) -> Optional[str]:
        if not properties:
            return None
        best_type = None
        best_score = 0.0
        type_groups: Dict[str, List[Node]] = defaultdict(list)
        for n in self.graph.nodes:
            type_groups[n.type].append(n)
        for node_type, nodes in type_groups.items():
            score = 0.0
            count = 0
            for n in nodes:
                for key, value in properties.items():
                    if key in n.properties and n.properties[key] == value:
                        score += 1
                count += 1
            avg = score / count if count > 0 else 0
            if avg > best_score:
                best_score = avg
                best_type = node_type
        return best_type

    def get_type_hierarchy(self) -> Dict[str, List[str]]:
        hierarchy: Dict[str, List[str]] = {}
        for node in self.graph.nodes:
            if node.type not in hierarchy:
                hierarchy[node.type] = []
        rels = self.graph.find_relationships_by_type("is_subtype_of")
        for rel in rels:
            src = self.graph.get_node(rel.source_id)
            tgt = self.graph.get_node(rel.target_id)
            if src and tgt:
                if tgt.type not in hierarchy:
                    hierarchy[tgt.type] = []
                hierarchy[tgt.type].append(src.type)
        return hierarchy

    def summarize_cluster(self, node_ids: List[str]) -> Dict[str, Any]:
        nodes = [self.graph.get_node(nid) for nid in node_ids]
        nodes = [n for n in nodes if n is not None]
        if not nodes:
            return {}
        types: Dict[str, int] = defaultdict(int)
        all_props: Dict[str, set] = defaultdict(set)
        for n in nodes:
            types[n.type] += 1
            for k, v in n.properties.items():
                all_props[k].add(v)
        edge_count = 0
        for rel in self.graph.relationships:
            if rel.source_id in node_ids and rel.target_id in node_ids:
                edge_count += 1
        return {
            "node_count": len(nodes),
            "types": dict(types),
            "properties": {k: list(v)[:5] for k, v in all_props.items()},
            "internal_relationships": edge_count,
            "density": round(
                edge_count / (len(nodes) * (len(nodes) - 1) + 1), 4
            ),
        }
