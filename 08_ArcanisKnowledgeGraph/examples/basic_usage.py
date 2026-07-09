"""Basic usage example for ArcanisKnowledgeGraph."""
from arcaniskg import ArcanisKnowledgeGraph

kg = ArcanisKnowledgeGraph()

alice = kg.add_node(type="person", properties={"name": "Alice", "role": "researcher"})
bob = kg.add_node(type="person", properties={"name": "Bob", "role": "engineer"})
project = kg.add_node(type="project", properties={"name": "ArcanisOS", "status": "active"})
idea = kg.add_node(type="idea", properties={"title": "AI scheduler", "priority": "high"})
task = kg.add_node(type="task", properties={"description": "Implement scheduler", "status": "in_progress"})

kg.add_relationship(alice.id, project.id, type="leads")
kg.add_relationship(bob.id, project.id, type="works_on")
kg.add_relationship(project.id, idea.id, type="generates")
kg.add_relationship(idea.id, task.id, type="creates")

print("=== Graph Info ===")
print(kg.info)

print("\n=== Graph Query ===")
result = kg.execute_query("MATCH (p:person)-[r]->(pr:project)")
for n in result.get("nodes", []):
    print(f"  Node: {n['type']} -> {n['properties']}")

print("\n=== BFS Traversal ===")
traversal = kg.traverser.bfs(alice.id, max_depth=3)
for n in traversal.nodes:
    print(f"  {n.type}: {n.properties}")

print("\n=== Find Path ===")
path = kg.traverser.find_shortest_path(alice.id, task.id)
if path:
    print(" -> ".join(n.type for n in path))

print("\n=== Visualization (DOT) ===")
print(kg.visualize.to_dot("ArcanisGraph"))
