"""Dependency graph for tracking file and target dependencies."""

import os
import hashlib
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class DependencyNode:
    def __init__(self, name: str, node_type: str = "file"):
        self.name = name
        self.node_type = node_type
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self.hash: Optional[str] = None
        self.mtime: Optional[float] = None

    def add_dependency(self, dep_name: str):
        self.dependencies.add(dep_name)

    def add_dependent(self, dep_name: str):
        self.dependents.add(dep_name)


class DependencyGraph:
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self._build_order_cache = None

    def add_node(self, name: str, node_type: str = "file") -> DependencyNode:
        if name not in self.nodes:
            self.nodes[name] = DependencyNode(name, node_type)
        return self.nodes[name]

    def add_edge(self, from_node: str, to_node: str):
        self.add_node(from_node).add_dependency(to_node)
        self.add_node(to_node).add_dependent(from_node)
        self._build_order_cache = None

    def get_dependencies(self, name: str) -> Set[str]:
        node = self.nodes.get(name)
        return node.dependencies if node else set()

    def get_dependents(self, name: str) -> Set[str]:
        node = self.nodes.get(name)
        return node.dependents if node else set()

    def get_leaf_nodes(self) -> List[str]:
        return [n for n, node in self.nodes.items() if not node.dependents]

    def get_root_nodes(self) -> List[str]:
        return [n for n, node in self.nodes.items() if not node.dependencies]

    def topological_sort(self) -> List[str]:
        if self._build_order_cache:
            return self._build_order_cache

        visited = set()
        temp_mark = set()
        order = []

        def visit(node_name):
            if node_name in temp_mark:
                raise ValueError(f"Circular dependency detected: {node_name}")
            if node_name not in visited:
                temp_mark.add(node_name)
                node = self.nodes.get(node_name)
                if node:
                    for dep in node.dependencies:
                        visit(dep)
                temp_mark.discard(node_name)
                visited.add(node_name)
                order.append(node_name)

        for node_name in list(self.nodes.keys()):
            if node_name not in visited:
                visit(node_name)

        self._build_order_cache = order
        return order

    def reverse_topological_sort(self) -> List[str]:
        return list(reversed(self.topological_sort()))

    def get_changed_files(self, file_hashes: Dict[str, str]) -> Set[str]:
        changed = set()
        for name, node in self.nodes.items():
            if node.node_type == "file":
                current_hash = file_hashes.get(name)
                if current_hash != node.hash:
                    changed.add(name)
        return changed

    def compute_affected_targets(self, changed_files: Set[str]) -> Set[str]:
        affected = set(changed_files)
        queue = list(changed_files)

        while queue:
            current = queue.pop(0)
            node = self.nodes.get(current)
            if node:
                for dependent in node.dependents:
                    if dependent not in affected:
                        affected.add(dependent)
                        queue.append(dependent)

        return affected

    def clear_cache(self):
        self._build_order_cache = None

    @staticmethod
    def compute_file_hash(filepath: str) -> Optional[str]:
        if not os.path.exists(filepath):
            return None
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def compute_file_mtime(filepath: str) -> Optional[float]:
        if not os.path.exists(filepath):
            return None
        return os.path.getmtime(filepath)
