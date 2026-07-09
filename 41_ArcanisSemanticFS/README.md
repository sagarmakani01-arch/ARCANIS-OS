# ArcanisSemanticFS

**Project ID:** 41-ArcanisSemanticFS
**Phase:** 2 — Integration (Q1–Q3 2028)
**Status:** Implemented
**Language:** Python

## Overview

AI-powered semantic file system that indexes files, generates embeddings, tracks relationships, and enables natural language search.

## Quick Start

```bash
pip install -e ".[ai]"
python -c "
from arcanis_semantic_fs import SemanticFSEngine, SemanticFSConfig
from pathlib import Path
engine = SemanticFSEngine(SemanticFSConfig(root_path=Path('.')))
engine.initialize()
engine.index_directory()
results = engine.search('authentication code')
for r in results:
    print(f'{r.score:.2f} {r.file.path}')
"
```

## Features

- **Semantic search** — Find files by meaning, not just name
- **Auto-tagging** — Extracts functions, classes, imports from code
- **Relationship tracking** — Discovers dependencies between files
- **Organization suggestions** — AI recommends folder structures
- **Dependency graph** — Trace impact of changes
- **Backward compatible** — Works without embedding model

## License

All rights reserved. ArcanisLabs — Sagar Makani.
