"""Tests for dependency graph."""

import os
import tempfile
import unittest

from arcanis_build.dependency import DependencyGraph


class TestDependencyGraph(unittest.TestCase):
    def setUp(self):
        self.graph = DependencyGraph()

    def test_add_node(self):
        self.graph.add_node("main.arc")
        self.assertIn("main.arc", self.graph.nodes)

    def test_add_edge(self):
        self.graph.add_edge("main.arc", "utils.arc")
        deps = self.graph.get_dependencies("main.arc")
        self.assertIn("utils.arc", deps)
        deps_of_utils = self.graph.get_dependents("utils.arc")
        self.assertIn("main.arc", deps_of_utils)

    def test_topological_sort_simple(self):
        self.graph.add_edge("main.arc", "utils.arc")
        self.graph.add_edge("utils.arc", "stdlib.arc")
        order = self.graph.topological_sort()
        self.assertEqual(order, ["stdlib.arc", "utils.arc", "main.arc"])

    def test_topological_sort_complex(self):
        self.graph.add_edge("app.arc", "net.arc")
        self.graph.add_edge("app.arc", "db.arc")
        self.graph.add_edge("net.arc", "ssl.arc")
        self.graph.add_edge("db.arc", "sql.arc")
        order = self.graph.topological_sort()
        self.assertIn("ssl.arc", order)
        self.assertIn("sql.arc", order)
        self.assertGreater(order.index("net.arc"), order.index("ssl.arc"))
        self.assertGreater(order.index("db.arc"), order.index("sql.arc"))
        self.assertGreater(order.index("app.arc"), order.index("net.arc"))
        self.assertGreater(order.index("app.arc"), order.index("db.arc"))

    def test_circular_dependency(self):
        self.graph.add_edge("a.arc", "b.arc")
        self.graph.add_edge("b.arc", "c.arc")
        self.graph.add_edge("c.arc", "a.arc")
        with self.assertRaises(ValueError):
            self.graph.topological_sort()

    def test_leaf_nodes(self):
        self.graph.add_edge("app.arc", "lib.arc")
        self.graph.add_edge("app.arc", "utils.arc")
        leaves = self.graph.get_leaf_nodes()
        self.assertIn("app.arc", leaves)

    def test_root_nodes(self):
        self.graph.add_edge("app.arc", "lib.arc")
        self.graph.add_edge("app.arc", "utils.arc")
        roots = self.graph.get_root_nodes()
        self.assertIn("lib.arc", roots)
        self.assertIn("utils.arc", roots)

    def test_affected_targets(self):
        self.graph.add_edge("app.arc", "lib.arc")
        self.graph.add_edge("lib.arc", "utils.arc")
        affected = self.graph.compute_affected_targets({"utils.arc"})
        self.assertIn("utils.arc", affected)
        self.assertIn("lib.arc", affected)
        self.assertIn("app.arc", affected)

    def test_file_hash(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            path = f.name
        try:
            h1 = DependencyGraph.compute_file_hash(path)
            h2 = DependencyGraph.compute_file_hash(path + ".nonexistent")
            self.assertIsNotNone(h1)
            self.assertIsNone(h2)
            self.assertEqual(len(h1), 64)
        finally:
            os.unlink(path)

    def test_changed_files(self):
        self.graph.add_node("file.arc")
        self.graph.nodes["file.arc"].hash = "oldhash"
        changed = self.graph.get_changed_files({"file.arc": "newhash"})
        self.assertIn("file.arc", changed)

    def test_unchanged_files(self):
        self.graph.add_node("file.arc")
        self.graph.nodes["file.arc"].hash = "samehash"
        changed = self.graph.get_changed_files({"file.arc": "samehash"})
        self.assertNotIn("file.arc", changed)


if __name__ == "__main__":
    unittest.main()
