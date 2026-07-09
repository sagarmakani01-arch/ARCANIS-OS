"""AI features example for ArcanisKnowledgeGraph."""
from arcaniskg import ArcanisKnowledgeGraph

kg = ArcanisKnowledgeGraph()

for name in ["Alice", "Bob", "Carol", "Dave"]:
    kg.add_node(type="person", properties={
        "name": name, "department": "Engineering", "level": "senior"
    })
kg.add_node(type="person", properties={
    "name": "Eve", "department": "Research", "level": "senior"
})

for name in ["Project X", "Project Y", "Project Z"]:
    kg.add_node(type="project", properties={
        "name": name, "status": "active"
    })

print("=== Discover by Shared Property ===")
created = kg.ai.discovery.discover_by_shared_property("department", "same_department")
print(f"Created {len(created)} relationships")

print("\n=== Discover by Property Similarity ===")
created = kg.ai.discovery.discover_by_property_similarity(
    ["department", "level"], "similar_role", 0.5
)
print(f"Created {len(created)} similarity relationships")

print("\n=== Semantic Similarity ===")
nodes = kg.graph.find_nodes_by_property("name", "Alice")
if nodes:
    similar = kg.ai.semantic.find_semantically_similar(nodes[0].id, max_results=3)
    for node, score in similar:
        print(f"  {node.properties.get('name')}: {score:.2f}")

print("\n=== Reasoning Query ===")
answer = kg.ai.reasoning.query("count nodes")
print(f"  {answer['answer']}")

print("\n=== Type Inference ===")
inferred = kg.ai.semantic.infer_node_type({"department": "Engineering"})
print(f"  Inferred type: {inferred}")
