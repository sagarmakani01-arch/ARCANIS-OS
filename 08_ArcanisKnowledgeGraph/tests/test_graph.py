import unittest
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.graph.graph import Graph


class TestNode(unittest.TestCase):
    def test_create_node(self):
        n = Node(id="n1", type="person", properties={"name": "Alice"})
        self.assertEqual(n.id, "n1")
        self.assertEqual(n.type, "person")
        self.assertEqual(n.get("name"), "Alice")

    def test_node_auto_id(self):
        n = Node()
        self.assertIsNotNone(n.id)

    def test_node_to_from_dict(self):
        n1 = Node(id="x", type="test", properties={"a": 1})
        d = n1.to_dict()
        n2 = Node.from_dict(d)
        self.assertEqual(n1.id, n2.id)
        self.assertEqual(n1.type, n2.type)
        self.assertEqual(n1.properties, n2.properties)


class TestRelationship(unittest.TestCase):
    def test_create_relationship(self):
        r = Relationship(source_id="a", target_id="b", type="knows")
        self.assertEqual(r.source_id, "a")
        self.assertEqual(r.target_id, "b")
        self.assertEqual(r.type, "knows")

    def test_relationship_to_from_dict(self):
        r1 = Relationship(source_id="a", target_id="b", type="knows", properties={"since": 2024})
        d = r1.to_dict()
        r2 = Relationship.from_dict(d)
        self.assertEqual(r1.id, r2.id)
        self.assertEqual(r1.type, r2.type)


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.n1 = self.graph.add_node(Node(id="1", type="person"))
        self.n2 = self.graph.add_node(Node(id="2", type="project"))
        self.n3 = self.graph.add_node(Node(id="3", type="idea"))

    def test_add_get_node(self):
        self.assertEqual(self.graph.node_count, 3)
        self.assertIsNotNone(self.graph.get_node("1"))
        self.assertIsNone(self.graph.get_node("99"))

    def test_remove_node(self):
        self.assertTrue(self.graph.remove_node("1"))
        self.assertIsNone(self.graph.get_node("1"))
        self.assertEqual(self.graph.node_count, 2)

    def test_add_relationship(self):
        r = self.graph.add_relationship(
            Relationship(source_id="1", target_id="2", type="works_on")
        )
        self.assertIsNotNone(r)
        self.assertEqual(self.graph.relationship_count, 1)

    def test_add_relationship_missing_source(self):
        with self.assertRaises(ValueError):
            self.graph.add_relationship(
                Relationship(source_id="99", target_id="2", type="x")
            )

    def test_get_neighbors(self):
        self.graph.add_relationship(Relationship(source_id="1", target_id="2", type="a"))
        self.graph.add_relationship(Relationship(source_id="2", target_id="3", type="b"))
        neighbors = self.graph.get_neighbors("2", "out")
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0].id, "3")

    def test_find_path(self):
        self.graph.add_relationship(Relationship(source_id="1", target_id="2", type="a"))
        self.graph.add_relationship(Relationship(source_id="2", target_id="3", type="b"))
        path = self.graph.find_path("1", "3")
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3)

    def test_find_nodes_by_type(self):
        nodes = self.graph.find_nodes_by_type("person")
        self.assertEqual(len(nodes), 1)

    def test_find_nodes_by_property(self):
        n = Node(id="4", type="test", properties={"key": "val"})
        self.graph.add_node(n)
        nodes = self.graph.find_nodes_by_property("key", "val")
        self.assertEqual(len(nodes), 1)

    def test_to_from_dict(self):
        self.graph.add_relationship(Relationship(source_id="1", target_id="2", type="r"))
        d = self.graph.to_dict()
        g2 = Graph.from_dict(d)
        self.assertEqual(g2.node_count, 3)
        self.assertEqual(g2.relationship_count, 1)

    def test_clear(self):
        self.graph.clear()
        self.assertEqual(self.graph.node_count, 0)
        self.assertEqual(self.graph.relationship_count, 0)


if __name__ == "__main__":
    unittest.main()
