from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship


class InferenceEngine:
    def __init__(self, graph: Graph):
        self.graph = graph

    def deduce_transitive(
        self, relationship_type: str, max_hops: int = 3
    ) -> List[Relationship]:
        created: List[Relationship] = []
        for _ in range(max_hops):
            added = self._deduce_one_level(relationship_type)
            created.extend(added)
            if not added:
                break
        return created

    def _deduce_one_level(self, rel_type: str) -> List[Relationship]:
        by_source: Dict[str, List[Relationship]] = defaultdict(list)
        for rel in self.graph.relationships:
            if rel.type == rel_type:
                by_source[rel.source_id].append(rel)
        created: List[Relationship] = []
        for source_id, out_rels in by_source.items():
            for rel_a in out_rels:
                mid_id = rel_a.target_id
                for rel_b in by_source.get(mid_id, []):
                    if rel_b.target_id == source_id:
                        continue
                    if self._has_relationship(source_id, rel_b.target_id, rel_type):
                        continue
                    inferred = Relationship(
                        source_id=source_id,
                        target_id=rel_b.target_id,
                        type=rel_type,
                        properties={
                            "inferred": True,
                            "path": f"{rel_a.id} -> {rel_b.id}",
                        },
                    )
                    try:
                        self.graph.add_relationship(inferred)
                        created.append(inferred)
                    except ValueError:
                        pass
        return created

    def _has_relationship(
        self, src: str, tgt: str, rel_type: str
    ) -> bool:
        for rel in self.graph.relationships:
            if (
                rel.source_id == src
                and rel.target_id == tgt
                and rel.type == rel_type
            ):
                return True
        return False

    def apply_rule(
        self,
        premise_rel_type: str,
        conclusion_rel_type: str,
        rule_name: str = "inferred_rule",
    ) -> List[Relationship]:
        created: List[Relationship] = []
        for premise in self.graph.find_relationships_by_type(premise_rel_type):
            source = self.graph.get_node(premise.source_id)
            target = self.graph.get_node(premise.target_id)
            if source is None or target is None:
                continue
            if self._has_relationship(
                source.id, target.id, conclusion_rel_type
            ):
                continue
            inferred = Relationship(
                source_id=source.id,
                target_id=target.id,
                type=conclusion_rel_type,
                properties={
                    "inferred": True,
                    "rule": rule_name,
                    "based_on": premise.id,
                },
            )
            try:
                self.graph.add_relationship(inferred)
                created.append(inferred)
            except ValueError:
                pass
        return created

    def generalize(self, node_ids: List[str]) -> Optional[Node]:
        nodes = [
            self.graph.get_node(nid) for nid in node_ids
        ]
        nodes = [n for n in nodes if n is not None]
        if not nodes:
            return None
        common_type = nodes[0].type
        for n in nodes[1:]:
            if n.type != common_type:
                common_type = "generalized"
        common_props: Dict[str, Any] = {}
        if nodes:
            sample = nodes[0].properties
            for key in sample:
                if all(
                    n.properties.get(key) == sample[key] for n in nodes
                ):
                    common_props[key] = sample[key]
        gen = Node(
            type=common_type,
            properties={
                **common_props,
                "_generalized_from": [n.id for n in nodes],
            },
        )
        self.graph.add_node(gen)
        for n in nodes:
            rel = Relationship(
                source_id=gen.id,
                target_id=n.id,
                type="generalizes",
                properties={"generalization_of": n.id},
            )
            self.graph.add_relationship(rel)
        return gen

    def find_abductive_explanations(
        self, target_node_id: str, max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        target = self.graph.get_node(target_node_id)
        if target is None:
            return []
        explanations: List[Dict[str, Any]] = []
        visited: Set[str] = set()
        def dfs(current_id: str, path: List[Relationship], depth: int):
            if depth > max_depth:
                return
            for rel in self.graph.get_node_relationships(current_id, "in"):
                if rel.id in visited:
                    continue
                visited.add(rel.id)
                path.append(rel)
                source = self.graph.get_node(rel.source_id)
                if source:
                    explanations.append(
                        {
                            "source": source.to_dict(),
                            "relationship": rel.to_dict(),
                            "path_length": depth,
                            "path": [r.to_dict() for r in list(path)],
                        }
                    )
                    dfs(source.id, path, depth + 1)
                path.pop()
        dfs(target_node_id, [], 1)
        explanations.sort(key=lambda x: x["path_length"])
        return explanations

    def query(self, question: str) -> Dict[str, Any]:
        q = question.lower().strip()
        if q.startswith("what is "):
            entity = q[8:].strip().rstrip("?")
            for n in self.graph.nodes:
                if entity in n.type.lower() or entity in str(n.properties).lower():
                    return {
                        "answer": f"{n.type} node ({n.id})",
                        "node": n.to_dict(),
                        "confidence": 0.7,
                    }
            return {"answer": f"No knowledge about '{entity}'", "confidence": 0.0}
        elif q.startswith("how is "):
            rest = q[7:].strip().rstrip("?")
            parts = rest.split(" related to ")
            if len(parts) == 2:
                a_name, b_name = parts
                a = self._find_node_by_name(a_name)
                b = self._find_node_by_name(b_name)
                if a and b:
                    path = self.graph.find_path(a.id, b.id)
                    if path:
                        return {
                            "answer": f"{a_name} is related to {b_name} through {len(path) - 1} hop(s)",
                            "path": [n.to_dict() for n in path],
                            "confidence": 0.8,
                        }
                    return {
                        "answer": f"No direct connection between '{a_name}' and '{b_name}'",
                        "confidence": 0.3,
                    }
            return {"answer": "Could not parse question", "confidence": 0.0}
        elif "count" in q and "node" in q:
            return {
                "answer": f"There are {self.graph.node_count} nodes in the graph",
                "count": self.graph.node_count,
                "confidence": 1.0,
            }
        return {"answer": "Question not understood", "confidence": 0.0}

    def _find_node_by_name(self, name: str) -> Optional[Node]:
        for n in self.graph.nodes:
            if (
                name == n.type.lower()
                or name == n.id.lower()
                or any(
                    name == str(v).lower()
                    for v in n.properties.values()
                )
            ):
                return n
        return None
