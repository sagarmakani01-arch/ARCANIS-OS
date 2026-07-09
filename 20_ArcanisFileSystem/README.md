# ArcanisFileSystem

A modern filesystem for ArcanisOS with AI-powered features.

## Features

### Core
- **Inode-based storage** with direct/indirect block pointers
- **Hierarchical directory** structure with B-tree lookups
- **POSIX permissions** + extended ACL support
- **Rich metadata** management with custom fields

### AI Features
- **Semantic embeddings** for file content understanding
- **Auto-indexing** with keyword extraction and tagging
- **Intelligent search** combining keyword, semantic, fuzzy, and regex modes
- **Smart organization** with rule-based file management

### Security
- **AES-256-GCM encryption** with key management
- **Access control lists** for fine-grained permissions
- **Snapshot-based recovery** with chain tracking
- **Comprehensive audit logging** for compliance

## Quick Start

```python
from core.filesystem import ArcanisFileSystem

# Create filesystem instance
fs = ArcanisFileSystem()

# Create files and directories
fs.create_file("/hello.txt", b"Hello, ArcanisOS!")
fs.create_directory("/documents")

# Read files
content = fs.read_file("/hello.txt")

# Search
results = fs.search("hello")

# Backup
snapshot = fs.snapshot("initial_backup")

# Cleanup
fs.unmount()
```

## Architecture

```
ArcanisFileSystem/
├── src/
│   ├── core/           # Inodes, blocks, directories, metadata
│   ├── permissions/    # POSIX, ACL, authentication
│   ├── security/       # Encryption, recovery, audit
│   ├── ai/             # Embeddings, indexing, search, organizer
│   └── storage/        # Memory and disk backends
├── tests/              # Comprehensive test suite
├── tools/              # CLI utilities (fsck, mount, backup)
└── docs/               # Documentation
```

## Tools

### Filesystem Check
```bash
python tools/arcanis_fsck.py
python tools/arcanis_fsck.py --repair
```

### Mount Utility
```bash
python tools/arcanis_mount.py mount /path source '{"backend": "memory"}'
python tools/arcanis_mount.py list
python tools/arcanis_mount.py unmount /
```

### Backup
```bash
python tools/arcanis_backup.py create "my backup" full
python tools/arcanis_backup.py list
python tools/arcanis_backup.py export backup_metadata.json
```

## Running Tests

```bash
python -m pytest tests/ -v
python -m pytest tests/test_core.py -v
python -m pytest tests/test_security.py -v
```

## License

MIT License - Arcanis Lab
