"""Start the REST API server for ArcanisKnowledgeGraph."""
from arcaniskg import ArcanisKnowledgeGraph
from arcaniskg.api.rest import serve

kg = ArcanisKnowledgeGraph()

alice = kg.add_node(type="person", properties={"name": "Alice", "role": "researcher"})
bob = kg.add_node(type="person", properties={"name": "Bob", "role": "engineer"})
project = kg.add_node(type="project", properties={"name": "ArcanisOS", "status": "active"})
idea = kg.add_node(type="idea", properties={"title": "AI-first design", "priority": "high"})

kg.add_relationship(alice.id, project.id, type="leads")
kg.add_relationship(bob.id, project.id, type="works_on")
kg.add_relationship(project.id, idea.id, type="inspires")

print(f"Graph seeded with {kg.graph.node_count} nodes and {kg.graph.relationship_count} relationships")
print("Starting REST API...")
serve(kg.graph, host="127.0.0.1", port=8080)
