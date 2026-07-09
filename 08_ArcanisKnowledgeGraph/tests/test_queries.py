import unittest
from arcaniskg.graph.graph import Graph
from arcaniskg.graph.node import Node
from arcaniskg.graph.relationship import Relationship
from arcaniskg.query.parser import parse_query, QueryParseError
from arcaniskg.query.executor import QueryExecutor


class TestQueryParser(unittest.TestCase):
    def test_parse_match(self):
        result = parse_query("MATCH (p:person)-[r]->(pr:project)")
        self.assertEqual(result["command"], "match")
        self.assertEqual(result["source_type"], "person")
        self.assertEqual(result["target_type"], "project")

    def test_parse_traverse(self):
        result = parse_query("TRAVERSE node1 BFS DEPTH 5")
        self.assertEqual(result["command"], "traverse")
        self.assertEqual(result["algorithm"], "bfs")
        self.assertEqual(result["max_depth"], 5)

    def test_parse_find_nodes(self):
        result = parse_query("FIND NODES BY TYPE person")
        self.assertEqual(result["command"], "find")
        self.assertEqual(result["target"], "nodes")
        self.assertEqual(result["value"], "person")

    def test_parse_path(self):
        result = parse_query("PATH a TO b DEPTH 6")
        self.assertEqual(result["command"], "path")
        self.assertEqual(result["from_id"], "a")
        self.assertEqual(result["to_id"], "b")
        self.assertEqual(result["max_depth"], 6)

    def test_parse_node_get(self):
        result = parse_query("NODE.GET abc123")
        self.assertEqual(result["command"], "node.get")
        self.assertEqual(result["node_id"], "abc123")

    def test_parse_empty(self):
        with self.assertRaises(QueryParseError):
            parse_query("")


class TestQueryExecutor(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.n1 = self.graph.add_node(Node(id="1", type="person", properties={"name": "Alice"}))
        self.n2 = self.graph.add_node(Node(id="2", type="project", properties={"name": "P1"}))
        self.n3 = self.graph.add_node(Node(id="3", type="idea", properties={"title": "I1"}))
        self.graph.add_relationship(Relationship(source_id="1", target_id="2", type="works_on"))
        self.graph.add_relationship(Relationship(source_id="2", target_id="3", type="generates"))
        self.executor = QueryExecutor(self.graph)

    def test_execute_match(self):
        result = self.executor.execute("MATCH (p:person)-[r]->(pr:project)")
        self.assertIn("nodes", result)
        self.assertIn("relationships", result)

    def test_execute_find_by_type(self):
        result = self.executor.execute("FIND NODES BY TYPE person")
        self.assertEqual(len(result["nodes"]), 1)

    def test_execute_find_by_property(self):
        result = self.executor.execute('FIND NODES BY PROPERTY name = Alice')
        self.assertEqual(len(result["nodes"]), 1)

    def test_execute_traverse(self):
        result = self.executor.execute("TRAVERSE 1 BFS DEPTH 3")
        self.assertIn("nodes", result)

    def test_execute_path(self):
        result = self.executor.execute("PATH 1 TO 3")
        self.assertTrue(result["found"])
        self.assertEqual(len(result["path"]), 3)

    def test_execute_node_get(self):
        result = self.executor.execute("NODE.GET 1")
        self.assertEqual(result["node"]["id"], "1")

    def test_execute_invalid(self):
        from arcaniskg.query.executor import QueryExecutionError
        with self.assertRaises(QueryExecutionError):
            self.executor.execute("INVALID COMMAND")


if __name__ == "__main__":
    unittest.main()
