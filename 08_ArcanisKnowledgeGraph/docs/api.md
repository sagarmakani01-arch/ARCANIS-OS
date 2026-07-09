# API Reference

## ArcanisKnowledgeGraph

### Constructor
```python
kg = ArcanisKnowledgeGraph()
```

### Properties
| Property | Returns | Description |
|----------|---------|-------------|
| `kg.version` | `str` | Version string |
| `kg.info` | `dict` | Node/relationship counts |
| `kg.graph` | `Graph` | Underlying graph object |
| `kg.ai` | `AIFacade` | AI sub-modules |

### Node Operations
```python
node = kg.add_node(id=None, type="generic", properties={})
node = kg.get_node(node_id)
removed = kg.remove_node(node_id)
```

### Relationship Operations
```python
rel = kg.add_relationship(source_id, target_id, type="related_to", id=None, properties={})
rel = kg.get_relationship(rel_id)
removed = kg.remove_relationship(rel_id)
```

### Query
```python
result = kg.execute_query("MATCH (p:person)-[r]->(pr:project)")
```

### Persistence
```python
kg.connect_database(arcanisdb_instance)
kg.save()
kg.load()
```

### Serialization
```python
data = kg.to_dict()
kg.from_dict(data)
```

## Graph Traverser

```python
traverser = kg.traverser
result = traverser.bfs(start_id, max_depth=5, direction="out", node_filter=None)
result = traverser.dfs(start_id, max_depth=10, direction="out", node_filter=None)
path = traverser.find_shortest_path(from_id, to_id)
paths = traverser.find_all_paths(from_id, to_id, max_depth=6)
subgraph = traverser.find_subgraph(node_ids, max_depth=2)
```

## AI

### Discovery
```python
kg.ai.discovery.discover_by_shared_property("department", "same_department")
kg.ai.discovery.discover_by_type_cooccurrence("co_occurs_with")
kg.ai.discovery.discover_by_property_similarity(["name", "role"], "similar_to", 0.5)
```

### Semantic
```python
similar = kg.ai.semantic.find_semantically_similar(node_id, max_results=10)
inferred_type = kg.ai.semantic.infer_node_type({"role": "engineer"})
cluster_summary = kg.ai.semantic.summarize_cluster([id1, id2, id3])
```

### Reasoning
```python
kg.ai.reasoning.deduce_transitive("reports_to", max_hops=3)
kg.ai.reasoning.apply_rule("works_on", "contributes_to", "project_member")
generalized = kg.ai.reasoning.generalize([id1, id2, id3])
explanations = kg.ai.reasoning.find_abductive_explanations(node_id)
answer = kg.ai.reasoning.query("What is ArcanisOS?")
```

## Visualization

```python
renderer = kg.visualize
dot_str = renderer.to_dot("MyGraph")
cytoscape = renderer.to_cytoscape_json()
visjs = renderer.to_visjs_json()
d3 = renderer.to_d3_json()
html = renderer.to_html("Interactive Graph")
```

## REST API

```python
from arcaniskg.api.rest import serve
serve(kg.graph, host="127.0.0.1", port=8080)
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Server status |
| GET | `/api/nodes` | List all nodes |
| POST | `/api/nodes` | Create a node |
| GET | `/api/nodes/<id>` | Get node by ID |
| DELETE | `/api/nodes/<id>` | Delete node |
| GET | `/api/relationships` | List all relationships |
| POST | `/api/relationships` | Create a relationship |
| GET | `/api/relationships/<id>` | Get relationship |
| DELETE | `/api/relationships/<id>` | Delete relationship |
| GET | `/api/query?q=<query>` | Execute query |
| POST | `/api/query` | Execute query (JSON body) |
| GET | `/api/graph/html` | Interactive HTML visualization |
| GET | `/api/graph/visualize?format=json` | Graph data |
| POST | `/api/ai/discover/shared` | Discover shared-property relationships |
| POST | `/api/ai/discover/similarity` | Discover similarity relationships |
| POST | `/api/ai/reasoning/transitive` | Deduce transitive relationships |
| POST | `/api/ai/reasoning/rule` | Apply a reasoning rule |
