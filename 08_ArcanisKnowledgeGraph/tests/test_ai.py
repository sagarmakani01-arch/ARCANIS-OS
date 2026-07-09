import unittest
from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.ai.discovery import RelationshipDiscovery
from arcaniskg.ai.semantic import SemanticAnalyzer
from arcaniskg.ai.reasoning import InferenceEngine


class TestRelationshipDiscovery(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        for i, name in enumerate(["A", "B", "C"]):
            self.graph.add_node(
                Node(id=f"p{i}", type="person", properties={"dept": "eng", "level": "senior"})
            )
        self.graph.add_node(
            Node(id="p3", type="person", properties={"dept": "research", "level": "junior"})
        )
        self.discovery = RelationshipDiscovery(self.graph)

    def test_discover_by_shared_property(self):
        created = self.discovery.discover_by_shared_property("dept", "same_dept")
        self.assertGreater(len(created), 0)

    def test_discover_by_property_similarity(self):
        created = self.discovery.discover_by_property_similarity(
            ["dept", "level"], "similar", 0.5
        )
        self.assertGreater(len(created), 0)


class TestSemanticAnalyzer(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.a = self.graph.add_node(Node(id="a", type="person", properties={"name": "Alice", "role": "dev"}))
        self.b = self.graph.add_node(Node(id="b", type="person", properties={"name": "Bob", "role": "dev"}))
        self.c = self.graph.add_node(Node(id="c", type="project", properties={"name": "P1"}))
        self.graph.add_relationship(Relationship(source_id="a", target_id="b", type="knows"))
        self.semantic = SemanticAnalyzer(self.graph)

    def test_find_semantically_similar(self):
        results = self.semantic.find_semantically_similar("a")
        self.assertGreater(len(results), 0)

    def test_infer_node_type(self):
        inferred = self.semantic.infer_node_type({"role": "dev"})
        self.assertEqual(inferred, "person")

    def test_summarize_cluster(self):
        summary = self.semantic.summarize_cluster(["a", "b"])
        self.assertIn("node_count", summary)
        self.assertEqual(summary["node_count"], 2)


class TestInferenceEngine(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.graph.add_node(Node(id="a", type="person"))
        self.graph.add_node(Node(id="b", type="person"))
        self.graph.add_node(Node(id="c", type="person"))
        self.graph.add_relationship(Relationship(source_id="a", target_id="b", type="reports_to"))
        self.graph.add_relationship(Relationship(source_id="b", target_id="c", type="reports_to"))
        self.reasoning = InferenceEngine(self.graph)

    def test_deduce_transitive(self):
        created = self.reasoning.deduce_transitive("reports_to", max_hops=2)
        self.assertGreater(len(created), 0)

    def test_apply_rule(self):
        created = self.reasoning.apply_rule("reports_to", "manages", "management_rule")
        self.assertGreater(len(created), 0)

    def test_generalize(self):
        gen = self.reasoning.generalize(["a", "b"])
        self.assertIsNotNone(gen)

    def test_query(self):
        answer = self.reasoning.query("count nodes")
        self.assertIn("answer", answer)
        self.assertEqual(answer["count"], 3)


if __name__ == "__main__":
    unittest.main()
