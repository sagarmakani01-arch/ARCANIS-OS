# Architecture

The ArcanisKnowledgeGraph follows the same composite/facade pattern as ArcanisDatabase.

## Overview

```
ArcanisKnowledgeGraph (facade)
├── Graph (in-memory store)
│   ├── Node           — typed entity with properties
│   └── Relationship   — directed edge with type and properties
├── QueryExecutor      — parses and executes graph queries
│   ├── QueryParser    — text-to-command parsing
│   └── GraphTraverser — BFS, DFS, path finding
├── AIFacade
│   ├── RelationshipDiscovery — auto-discover relationships
│   ├── SemanticAnalyzer     — similarity and type inference
│   └── InferenceEngine      — reasoning and deduction
├── GraphRenderer     — DOT, Vis.js, Cytoscape, HTML output
├── DatabaseAdapter   — persist/load via ArcanisDatabase
└── REST API          — HTTP server for remote access
```

## Data Model

- **Node**: `{ id: str, type: str, properties: dict }`
- **Relationship**: `{ id: str, source_id: str, target_id: str, type: str, properties: dict }`

The graph maintains two adjacency indexes (`_adj_out`, `_adj_in`) for O(1) neighbor lookups.

## Query Language

| Command | Example |
|---------|---------|
| MATCH   | `MATCH (p:person)-[r]->(pr:project)` |
| FIND    | `FIND NODES BY TYPE person` |
| TRAVERSE | `TRAVERSE <id> BFS DEPTH 3` |
| PATH    | `PATH <from> TO <to>` |
| NODE.GET | `NODE.GET <id>` |
| REL.GET | `REL.GET <id>` |

## AI Pipeline

1. **Discovery** scans existing nodes for shared property values or type patterns and creates new relationships.
2. **Semantic** analysis scores similarity between nodes based on type, properties, and shared neighbors.
3. **Reasoning** applies transitive closure, user-defined rules, generalization, and abductive explanation.
