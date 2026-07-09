# ArcanisResearch

Maintain technical knowledge for the ecosystem through research documentation.

## Research Areas

- Operating systems
- AI
- Robotics
- Programming languages
- Hardware
- Security
- Mathematics

## Features

- Notes
- Papers
- Summaries
- Design comparisons

## Data Structure

### Database

- SQLite database with schema.sql

### Content

- **notes/**: Raw research notes and insights
- **papers/**: Research papers and academic articles
- **summaries/**: Concise summaries of research
- **comparisons/**: Design comparisons and analyses
- **README/**: Project documentation and configuration

## Usage

```bash
# Initialize the database
python -m database.init

# Search research entries
python -m database.search --query "keyword"

# Add new research entry
python -m database.add --file path/to/file.txt --type note --area operating-systems
```

## Database Schema

See `database/schema.sql` for the complete SQLite schema.

## Future Work

- Implement semantic search using Faiss
- Add web interface for browsing
- Integrate with citation managers
- Create API endpoints for data access
