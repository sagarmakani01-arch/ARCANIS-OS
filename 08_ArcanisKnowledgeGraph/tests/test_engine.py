import unittest
from arcaniskg import ArcanisKnowledgeGraph


class TestArcanisKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        self.kg = ArcanisKnowledgeGraph()

    def test_version(self):
        self.assertEqual(self.kg.version, "0.1.0")

    def test_info(self):
        info = self.kg.info
        self.assertIn("version", info)
        self.assertIn("nodes", info)

    def test_add_get_node(self):
        n = self.kg.add_node(type="test", properties={"k": "v"})
        self.assertIsNotNone(n.id)
        self.assertEqual(self.kg.get_node(n.id).id, n.id)

    def test_remove_node(self):
        n = self.kg.add_node()
        self.assertTrue(self.kg.remove_node(n.id))
        self.assertIsNone(self.kg.get_node(n.id))

    def test_add_relationship(self):
        a = self.kg.add_node()
        b = self.kg.add_node()
        r = self.kg.add_relationship(a.id, b.id, type="connected")
        self.assertIsNotNone(r.id)

    def test_execute_query(self):
        a = self.kg.add_node(type="person")
        b = self.kg.add_node(type="project")
        self.kg.add_relationship(a.id, b.id, type="works_on")
        result = self.kg.execute_query("MATCH (p:person)-[r]->(pr:project)")
        self.assertIn("nodes", result)

    def test_to_from_dict(self):
        self.kg.add_node(id="n1", type="t1")
        self.kg.add_node(id="n2", type="t2")
        self.kg.add_relationship("n1", "n2", type="r1")
        data = self.kg.to_dict()
        self.kg2 = ArcanisKnowledgeGraph()
        self.kg2.from_dict(data)
        self.assertEqual(self.kg2.graph.node_count, 2)
        self.assertEqual(self.kg2.graph.relationship_count, 1)

    def test_clear(self):
        self.kg.add_node()
        self.kg.add_node()
        self.kg.clear()
        self.assertEqual(self.kg.graph.node_count, 0)

    def test_context_manager(self):
        with ArcanisKnowledgeGraph() as kg:
            kg.add_node()
        self.assertEqual(kg.graph.node_count, 0)

    def test_ai_facade(self):
        self.assertIsNotNone(self.kg.ai.discovery)
        self.assertIsNotNone(self.kg.ai.semantic)
        self.assertIsNotNone(self.kg.ai.reasoning)

    def test_traverser(self):
        self.assertIsNotNone(self.kg.traverser)

    def test_visualize(self):
        self.assertIsNotNone(self.kg.visualize)


if __name__ == "__main__":
    unittest.main()
