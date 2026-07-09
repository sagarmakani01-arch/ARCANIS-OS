"""Integration with ArcanisDatabase example."""
from arcaniskg import ArcanisKnowledgeGraph

kg = ArcanisKnowledgeGraph()

alice = kg.add_node(type="person", properties={"name": "Alice", "role": "researcher"})
bob = kg.add_node(type="person", properties={"name": "Bob", "role": "engineer"})
project = kg.add_node(type="project", properties={"name": "ArcanisOS"})
kg.add_relationship(alice.id, project.id, type="works_on")
kg.add_relationship(bob.id, project.id, type="works_on")

try:
    from arcanisdb import ArcanisDatabase
    db = ArcanisDatabase(":memory:")
    kg.connect_database(db)
    kg.save()

    kg2 = ArcanisKnowledgeGraph()
    kg2.connect_database(db)
    kg2.load()
    print(f"Loaded {kg2.graph.node_count} nodes from database")

except ImportError:
    print("arcanisdb not installed. Install it to use persistence features.")

print("\nGraph data:")
for n in kg.graph.nodes:
    print(f"  {n.type}: {n.properties}")
