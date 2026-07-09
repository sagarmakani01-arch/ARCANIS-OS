from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship


class RelationshipDiscovery:
    def __init__(self, graph: Graph):
        self.graph = graph

    def discover_by_shared_property(
        self,
        property_key: str,
        relationship_type: str = "shares_property",
        min_shared: int = 1,
    ) -> List[Relationship]:
        value_groups: Dict[Any, List[Node]] = defaultdict(list)
        for node in self.graph.nodes:
            val = node.properties.get(property_key)
            if val is not None:
                value_groups[val].append(node)
        created: List[Relationship] = []
        for val, nodes in value_groups.items():
            if len(nodes) < min_shared:
                continue
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    rel = Relationship(
                        source_id=nodes[i].id,
                        target_id=nodes[j].id,
                        type=relationship_type,
                        properties={"shared_key": property_key, "shared_value": val},
                    )
                    try:
                        self.graph.add_relationship(rel)
                        created.append(rel)
                    except ValueError:
                        pass
        return created

    def discover_by_type_cooccurrence(
        self,
        relationship_type: str = "co_occurs_with",
    ) -> List[Relationship]:
        type_nodes: Dict[str, List[Node]] = defaultdict(list)
        for node in self.graph.nodes:
            type_nodes[node.type].append(node)
        created: List[Relationship] = []
        types = list(type_nodes.keys())
        for i in range(len(types)):
            for j in range(i + 1, len(types)):
                score = len(type_nodes[types[i]]) + len(type_nodes[types[j]])
                for src in type_nodes[types[i]]:
                    for tgt in type_nodes[types[j]]:
                        if self._has_existing_rel(src.id, tgt.id):
                            continue
                        rel = Relationship(
                            source_id=src.id,
                            target_id=tgt.id,
                            type=relationship_type,
                            properties={
                                "source_type": types[i],
                                "target_type": types[j],
                                "strength": score,
                            },
                        )
                        try:
                            self.graph.add_relationship(rel)
                            created.append(rel)
                        except ValueError:
                            pass
        return created

    def discover_by_property_similarity(
        self,
        property_keys: List[str],
        relationship_type: str = "similar_to",
        threshold: float = 0.5,
    ) -> List[Relationship]:
        created: List[Relationship] = []
        nodes = self.graph.nodes
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                score = self._compute_similarity(
                    nodes[i], nodes[j], property_keys
                )
                if score >= threshold:
                    rel = Relationship(
                        source_id=nodes[i].id,
                        target_id=nodes[j].id,
                        type=relationship_type,
                        properties={"similarity_score": round(score, 4)},
                    )
                    try:
                        self.graph.add_relationship(rel)
                        created.append(rel)
                    except ValueError:
                        pass
        return created

    def _compute_similarity(
        self, a: Node, b: Node, keys: List[str]
    ) -> float:
        matches = 0
        total = 0
        for key in keys:
            va = a.properties.get(key)
            vb = b.properties.get(key)
            if va is not None and vb is not None:
                total += 1
                if va == vb:
                    matches += 1
            elif va is None and vb is None:
                total += 1
                matches += 1
        if total == 0:
            return 0.0
        return matches / total

    def _has_existing_rel(self, src_id: str, tgt_id: str) -> bool:
        for rel in self.graph.relationships:
            if (rel.source_id == src_id and rel.target_id == tgt_id) or (
                rel.source_id == tgt_id and rel.target_id == src_id
            ):
                return True
        return False
