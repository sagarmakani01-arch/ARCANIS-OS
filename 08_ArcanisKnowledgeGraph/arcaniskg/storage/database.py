from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship


class DatabaseAdapter:
    def __init__(self, db: Any):
        self.db = db
        self._ensure_collections()

    def _ensure_collections(self) -> None:
        try:
            self.db.structured.create_collection("kg_nodes")
        except Exception:
            pass
        try:
            self.db.structured.create_collection("kg_relationships")
        except Exception:
            pass

    def save_graph(self, graph: Graph) -> None:
        for node in graph.nodes:
            self._save_node(node)
        for rel in graph.relationships:
            self._save_relationship(rel)

    def _save_node(self, node: Node) -> None:
        record = {
            "graph_node_id": node.id,
            "type": node.type,
            "properties": json.dumps(node.properties),
        }
        existing = self.db.structured.query(
            "kg_nodes", {"graph_node_id": node.id}
        )
        if existing:
            self.db.structured.update(
                "kg_nodes", existing[0]["_id"], record
            )
        else:
            self.db.structured.insert("kg_nodes", record)

    def _save_relationship(self, rel: Relationship) -> None:
        record = {
            "graph_rel_id": rel.id,
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "type": rel.type,
            "properties": json.dumps(rel.properties),
        }
        existing = self.db.structured.query(
            "kg_relationships", {"graph_rel_id": rel.id}
        )
        if existing:
            self.db.structured.update(
                "kg_relationships", existing[0]["_id"], record
            )
        else:
            self.db.structured.insert("kg_relationships", record)

    def load_graph(self) -> Graph:
        graph = Graph()
        node_records = self.db.structured.query("kg_nodes", {})
        for rec in node_records:
            node = Node(
                id=rec["graph_node_id"],
                type=rec.get("type", "generic"),
                properties=json.loads(rec.get("properties", "{}")),
            )
            graph.add_node(node)
        rel_records = self.db.structured.query("kg_relationships", {})
        for rec in rel_records:
            rel = Relationship(
                source_id=rec["source_id"],
                target_id=rec["target_id"],
                type=rec.get("type", "related_to"),
                id=rec["graph_rel_id"],
                properties=json.loads(rec.get("properties", "{}")),
            )
            try:
                graph.add_relationship(rel)
            except ValueError:
                pass
        return graph

    def sync_to_database(self, graph: Graph) -> None:
        self.save_graph(graph)

    def sync_from_database(self, graph: Graph) -> Graph:
        return self.load_graph()
