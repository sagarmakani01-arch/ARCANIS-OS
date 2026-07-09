import unittest
from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.visualization.renderer import GraphRenderer


class TestGraphRenderer(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.graph.add_node(Node(id="n1", type="person", properties={"name": "Alice"}))
        self.graph.add_node(Node(id="n2", type="project", properties={"name": "P1"}))
        self.graph.add_relationship(Relationship(source_id="n1", target_id="n2", type="works_on"))
        self.renderer = GraphRenderer(self.graph)

    def test_to_dot(self):
        dot = self.renderer.to_dot("Test")
        self.assertIn("digraph", dot)
        self.assertIn("n1", dot)
        self.assertIn("n2", dot)
        self.assertIn("works_on", dot)

    def test_to_cytoscape_json(self):
        data = self.renderer.to_cytoscape_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(len(data["edges"]), 1)

    def test_to_visjs_json(self):
        data = self.renderer.to_visjs_json()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)

    def test_to_html(self):
        html = self.renderer.to_html()
        self.assertIn("vis-network", html)
        self.assertIn("<!DOCTYPE html>", html)


if __name__ == "__main__":
    unittest.main()
