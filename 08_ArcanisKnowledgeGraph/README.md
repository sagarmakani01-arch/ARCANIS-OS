# ArcanisKnowledgeGraph

A knowledge graph engine for the Arcanis ecosystem. Represents relationships between information — people, projects, files, ideas, tasks — with graph queries, AI-powered discovery, and interactive visualization.

## Features

### Core
- **Nodes** — typed entities with arbitrary properties
- **Relationships** — directed, typed edges between nodes
- **Graph Queries** — pattern matching, traversal (BFS/DFS), path finding
- **Graph Visualization** — DOT, Cytoscape.js, Vis.js, D3.js, interactive HTML

### AI
- **Automatic Relationship Discovery** — shared properties, type co-occurrence, property similarity
- **Semantic Connections** — semantic similarity scoring, type inference, cluster summarization
- **Knowledge Reasoning** — transitive deduction, rule-based inference, generalization, abductive reasoning

### Integration
- **ArcanisDatabase** — persist/load graphs via the ArcanisDB structured store
- **ArcanisBrain** — (to be connected) semantic querying and reasoning bridge
- **REST API** — built-in HTTP server for remote graph access

## Quick Start

```python
from arcaniskg import ArcanisKnowledgeGraph

kg = ArcanisKnowledgeGraph()

node_a = kg.add_node(type="person", properties={"name": "Alice", "role": "researcher"})
node_b = kg.add_node(type="project", properties={"name": "ArcanisOS", "status": "active"})
kg.add_relationship(node_a.id, node_b.id, type="works_on")

result = kg.execute_query("MATCH (p:person)-[r]->(pr:project)")
print(result)
```

## REST API

```python
from arcaniskg.api.rest import serve
serve(kg.graph, host="127.0.0.1", port=8080)
```

Then open http://127.0.0.1:8080/api/graph/html for interactive visualization.

## Project Structure

```
arcaniskg/
├── __init__.py             Package entry, exports ArcanisKnowledgeGraph
├── engine.py               Main facade class
├── graph/
│   ├── node.py             Node data type
│   ├── relationship.py     Relationship data type
│   └── graph.py            In-memory graph with adjacency tracking
├── query/
│   ├── parser.py           Query language parser
│   ├── executor.py         Query execution engine
│   └── traverser.py        BFS/DFS traversal and path finding
├── ai/
│   ├── discovery.py        Automatic relationship discovery
│   ├── semantic.py         Semantic analysis and similarity
│   └── reasoning.py        Deductive, rule-based, abductive reasoning
├── visualization/
│   └── renderer.py         DOT, JSON, and interactive HTML rendering
├── storage/
│   └── database.py         ArcanisDatabase persistence adapter
└── api/
    └── rest.py             Built-in HTTP REST API server
```

## Dependencies

- Python 3.8+
- (Optional) `arcanisdb` for database persistence
- (Optional) `numpy` for vector similarity operations
