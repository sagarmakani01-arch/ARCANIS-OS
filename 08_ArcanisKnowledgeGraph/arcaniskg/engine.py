from __future__ import annotations
from typing import Any, Dict, List, Optional

from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.query.executor import QueryExecutor
from arcaniskg.query.traverser import GraphTraverser
from arcaniskg.visualization.renderer import GraphRenderer
from arcaniskg.ai.discovery import RelationshipDiscovery
from arcaniskg.ai.semantic import SemanticAnalyzer
from arcaniskg.ai.reasoning import InferenceEngine


class AIFacade:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.discovery = RelationshipDiscovery(graph)
        self.semantic = SemanticAnalyzer(graph)
        self.reasoning = InferenceEngine(graph)


class ArcanisKnowledgeGraph:
    def __init__(self):
        self.graph = Graph()
        self.query = QueryExecutor(self.graph)
        self.traverser = GraphTraverser(self.graph)
        self.visualize = GraphRenderer(self.graph)
        self.ai = AIFacade(self.graph)
        self._db_adapter: Optional[object] = None

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def info(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "nodes": self.graph.node_count,
            "relationships": self.graph.relationship_count,
            "node_types": list({n.type for n in self.graph.nodes}),
            "relationship_types": list({r.type for r in self.graph.relationships}),
        }

    def add_node(
        self,
        id: Optional[str] = None,
        type: str = "generic",
        properties: Optional[Dict[str, Any]] = None,
    ) -> Node:
        node = Node(id=id, type=type, properties=properties)
        self.graph.add_node(node)
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self.graph.get_node(node_id)

    def remove_node(self, node_id: str) -> bool:
        return self.graph.remove_node(node_id)

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        type: str = "related_to",
        id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Relationship:
        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            type=type,
            id=id,
            properties=properties,
        )
        return self.graph.add_relationship(rel)

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        return self.graph.get_relationship(rel_id)

    def remove_relationship(self, rel_id: str) -> bool:
        return self.graph.remove_relationship(rel_id)

    def connect_database(self, db: Any) -> None:
        from arcaniskg.storage.database import DatabaseAdapter
        self._db_adapter = DatabaseAdapter(db)

    def save(self) -> None:
        if self._db_adapter:
            self._db_adapter.save_graph(self.graph)

    def load(self) -> None:
        if self._db_adapter:
            self.graph = self._db_adapter.load_graph()
            self._rebind()

    def _rebind(self) -> None:
        self.query = QueryExecutor(self.graph)
        self.traverser = GraphTraverser(self.graph)
        self.visualize = GraphRenderer(self.graph)
        self.ai = AIFacade(self.graph)

    def execute_query(self, query_text: str) -> Dict[str, Any]:
        return self.query.execute(query_text)

    def to_dict(self) -> Dict[str, Any]:
        return self.graph.to_dict()

    def from_dict(self, data: Dict[str, Any]) -> None:
        self.graph = Graph.from_dict(data)
        self._rebind()

    def clear(self) -> None:
        self.graph.clear()

    def close(self) -> None:
        self.clear()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
