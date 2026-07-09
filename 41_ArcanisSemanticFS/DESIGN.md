# Semantic File System — Design Document

**Project ID:** 41-ArcanisSemanticFS
**Phase:** 1 — Q4 2027 (Design Document)
**Status:** Design

---

## 1. Overview

The Semantic File System (SFS) extends traditional file systems with AI-powered metadata, semantic search, and content-aware organization. Files are not just named paths — they are entities with embeddings, relationships, and intent.

## 2. Design Goals

| Goal | Description |
|------|-------------|
| **Semantic Search** | Find files by meaning, not just name |
| **Auto-Organization** | AI suggests folder structures based on content |
| **Relationship Tracking** | Files know their dependencies and related files |
| **Intent-Aware** | System understands *why* a file exists |
| **Backward Compatible** | Existing programs work without modification |
| **Privacy-First** | Embeddings computed on-device, never leave the machine |

## 3. Architecture

```
┌─────────────────────────────────────────────────┐
│                User Applications                 │
│  (ArcanisShell, ArcanisIDE, ArcanisDesktop)      │
├─────────────────────────────────────────────────┤
│              Semantic FS Interface               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │  VFS     │ │ Semantic │ │ Relationship     ││
│  │  Layer   │ │ Index    │ │ Graph            ││
│  └──────────┘ └──────────┘ └──────────────────┘│
├─────────────────────────────────────────────────┤
│              Storage Backend                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │  Block   │ │ Metadata │ │ Embedding        ││
│  │  Device  │ │ Store    │ │ Store            ││
│  └──────────┘ └──────────┘ └──────────────────┘│
└─────────────────────────────────────────────────┘
```

## 4. Data Model

### 4.1 File Entity

```
FileEntity {
    id: UUID
    path: String                    # Traditional path
    name: String                    # File name
    content_type: String            # MIME type
    size: UInt64
    created_at: Timestamp
    modified_at: Timestamp
    
    # Semantic metadata
    embedding: Vector[384]          # Semantic embedding
    tags: Set[String]               # Auto-generated tags
    summary: String                 # AI-generated summary
    intent: String                  # Why this file exists
    
    # Relationships
    depends_on: Set[UUID]           # Files this depends on
    depended_by: Set[UUID]          # Files that depend on this
    related: Set[UUID]              # Semantically similar files
    lineage: List[UUID]             # Creation/edit history
}
```

### 4.2 Folder Entity

```
FolderEntity {
    id: UUID
    path: String
    name: String
    purpose: String                 # AI-determined purpose
    suggested_by: UUID?             # Which AI suggested this layout
    auto_organized: Bool
}
```

### 4.3 Relationship Types

| Relationship | Description | Example |
|-------------|-------------|---------|
| `depends_on` | A imports/requires B | `app.py` depends_on `utils.py` |
| `derived_from` | A was created from B | `output.csv` derived_from `raw_data.json` |
| `similar_to` | A is semantically similar to B | Two README files in different repos |
| `version_of` | A is a version of B | `v2.py` version_of `v1.py` |
| `test_for` | A tests B | `test_app.py` test_for `app.py` |
| `config_for` | A configures B | `config.yaml` config_for `app.py` |

## 5. Core Operations

### 5.1 Semantic Search

```python
# Natural language query
sfs.search("find the Python file that handles user authentication")

# Content-based search
sfs.search_similar("path/to/file.py", top_k=10)

# Tag-based search
sfs.search_by_tag(["authentication", "security"])

# Combined search
sfs.search("authentication code", filters={"language": "python", "modified_after": "2027-01-01"})
```

### 5.2 Auto-Organization

```python
# Analyze project and suggest folder structure
suggestion = sfs.suggest_organization("path/to/project")
# Returns:
# {
#   "current": {"files": 45, "folders": 8, "score": 0.6},
#   "suggested": {
#     "src/": {"purpose": "Source code", "files": 25},
#     "tests/": {"purpose": "Test files", "files": 12},
#     "docs/": {"purpose": "Documentation", "files": 5},
#     "config/": {"purpose": "Configuration", "files": 3}
#   },
#   "confidence": 0.87
# }

# Apply suggestion
sfs.apply_organization(suggestion, dry_run=True)
```

### 5.3 Relationship Discovery

```python
# Find related files
related = sfs.get_related("path/to/main.py")

# Get dependency graph
graph = sfs.dependency_graph("path/to/main.py", depth=3)

# Find impact of changing a file
impact = sfs.impact_analysis("path/to/utils.py")
```

## 6. Embedding Pipeline

```
File Created/Modified
        │
        ▼
┌──────────────────┐
│  Content Extract  │  Extract text, code, structure
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Chunking         │  Split into meaningful chunks
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Embedding        │  all-MiniLM-L6-v2 (on-device)
│  Generation       │  384-dimensional vectors
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Index Update     │  Update vector index + metadata
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Relationship     │  Discover related files
│  Discovery        │  Update relationship graph
└──────────────────┘
```

## 7. Storage Schema

### 7.1 Metadata Store (SQLite)

```sql
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    content_type TEXT,
    size INTEGER,
    created_at TEXT,
    modified_at TEXT,
    summary TEXT,
    intent TEXT,
    tags TEXT  -- JSON array
);

CREATE TABLE relationships (
    source_id TEXT,
    target_id TEXT,
    type TEXT,
    confidence REAL,
    created_at TEXT,
    PRIMARY KEY (source_id, target_id, type)
);
```

### 7.2 Embedding Store (FAISS / sqlite-vss)

```sql
CREATE VIRTUAL TABLE embeddings USING vector_sink(
    id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);
```

## 8. Privacy Model

| Data | Storage | Leaves Device |
|------|---------|---------------|
| File content | Local disk | Never |
| Embeddings | Local SQLite | Never |
| Metadata | Local SQLite | Never |
| AI summaries | Local only | Never |
| Relationship graph | Local only | Never |

All embedding generation runs on-device using `sentence-transformers`.

## 9. Performance Targets

| Operation | Target Latency |
|-----------|---------------|
| File indexing (1KB) | <50ms |
| Semantic search (1M files) | <200ms |
| Relationship discovery | <100ms |
| Auto-organization suggestion | <2s |
| Embedding generation (per file) | <100ms |

## 10. Integration Points

```
ArcanisShell     → semantic search, auto-organization
ArcanisIDE       → related files, dependency graph
ArcanisDesktop   → smart file browser, tagging
ArcanisBrain     → intent understanding, context
ArcanisKnowledgeGraph → shared entity model
```

## 11. Implementation Phases

| Phase | Deliverable | Target |
|-------|-------------|--------|
| Phase 1 (Q4 2027) | Design document (this) | Complete |
| Phase 2 (Q1 2028) | Metadata store + basic indexing | Prototype |
| Phase 2 (Q2 2028) | Embedding pipeline + search | Beta |
| Phase 2 (Q3 2028) | Relationship graph + auto-org | Beta |
| Phase 3 (Q4 2028) | Full integration with ecosystem | Release |

---

*Design document. Implementation begins Phase 2.*
