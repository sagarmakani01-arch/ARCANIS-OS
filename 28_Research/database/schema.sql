# ArcanisResearch Database

This directory contains the SQLite database and metadata for the research knowledge base.

## Database Schema

### research_entries
Stores all research materials (notes, papers, summaries, comparisons)

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- title (TEXT)
- type (TEXT) - 'note', 'paper', 'summary', 'comparison'
- content (TEXT)
- research_area (TEXT) - 'operating-systems', 'ai', 'robotics', 'programming-languages', 'hardware', 'security', 'mathematics'
- created_at (TEXT)
- updated_at (TEXT)
- file_path (TEXT)
- metadata (TEXT) - JSON fields for paper URLs, comparison entities, etc.

### tags
Many-to-many relationship for tagging entries

### entry_tags
Junction table

### embeddings
For semantic search (Faiss)

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- entry_id (INTEGER)
- embedding (BLOB)
- model (TEXT)
