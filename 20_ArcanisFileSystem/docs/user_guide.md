# ArcanisFileSystem User Guide

## Installation

ArcanisFileSystem requires Python 3.8+ with no external dependencies.

```bash
# Clone or download the source
cd 20_ArcanisFileSystem

# Run tests
python -m pytest tests/ -v
```

## Basic Usage

### Creating a Filesystem

```python
from core.filesystem import ArcanisFileSystem

# In-memory filesystem (for testing)
fs = ArcanisFileSystem()

# Or with disk persistence
from storage.disk import DiskBackend
backend = DiskBackend("/path/to/storage")
fs = ArcanisFileSystem(storage_backend=backend)
```

### Working with Files

```python
# Create a file
fs.create_file("/hello.txt", b"Hello, World!")

# Read a file
content = fs.read_file("/hello.txt")
print(content)  # b'Hello, World!'

# Write (overwrite)
fs.write_file("/hello.txt", b"Updated content")

# Append
fs.write_file("/hello.txt", b" more", append=True)

# Get file info
info = fs.stat("/hello.txt")
print(info["size"], info["permissions"])
```

### Working with Directories

```python
# Create directory
fs.create_directory("/documents")

# Create nested directories
fs.create_directory("/documents/projects")
fs.create_directory("/documents/projects/arc")

# List directory
entries = fs.list_directory("/documents")
for entry in entries:
    print(entry.name, entry.entry_type)
```

### Permissions

```python
# Set permissions
fs.chmod("/hello.txt", 0o755)

# Check permissions
info = fs.stat("/hello.txt")
print(info["permissions"])  # '0o755'
```

### Encryption

```python
# Encrypt a file
fs.encrypt_file("/secret.txt")

# Reading encrypted files works transparently
content = fs.read_file("/secret.txt")
```

### Snapshots and Recovery

```python
# Create a snapshot
snap = fs.snapshot("before_changes")
print(f"Snapshot {snap.id} created")

# List snapshots
for s in fs._recovery.list_snapshots():
    print(s.name, s.status)
```

### AI-Powered Search

```python
# Index all files first
fs.index_all()

# Search by content
results = fs.search("python tutorial")
for result in results:
    print(result.path, result.score)
```

## CLI Tools

### Filesystem Check (fsck)

```bash
# Check filesystem integrity
python tools/arcanis_fsck.py

# Check and repair
python tools/arcanis_fsck.py --repair
```

### Mount Utility

```bash
# List mounts
python tools/arcanis_mount.py list
```

### Backup

```bash
# Create backup
python tools/arcanis_backup.py create "my backup" full

# List backups
python tools/arcanis_backup.py list

# Export metadata
python tools/arcanis_backup.py export backup_info.json
```

## Architecture Overview

```
┌─────────────────────────────────────────┐
│          ArcanisFileSystem              │
├─────────────────────────────────────────┤
│  Core: Inodes, Blocks, Directories      │
├─────────────────────────────────────────┤
│  Permissions: POSIX, ACL, Auth          │
├─────────────────────────────────────────┤
│  Security: Encryption, Recovery, Audit  │
├─────────────────────────────────────────┤
│  AI: Embeddings, Indexer, Search        │
├─────────────────────────────────────────┤
│  Storage: Memory / Disk Backend         │
└─────────────────────────────────────────┘
```

## Examples

### Photo Organizer

```python
from core.filesystem import ArcanisFileSystem
from ai.organizer import SmartOrganizer, OrganizationRule, OrganizeAction, MatchCondition

fs = ArcanisFileSystem()

# Create organization rules
organizer = SmartOrganizer()
organizer.add_rule(OrganizationRule(
    name="Photos by Date",
    conditions=[(MatchCondition.EXTENSION, "jpg")],
    action=OrganizeAction.MOVE,
    target_path="/Photos/{year}/{month}/{name}{ext}"
))

# Process files
for entry in fs.list_directory("/inbox"):
    if entry.entry_type == 0:  # FILE
        info = fs.stat(f"/{entry.name}")
        actions = organizer.organize_file(entry.inode_id, info)
        for action in actions:
            print(f"Moved {entry.name} to {action.target_path}")
```

### Document Search

```python
from core.filesystem import ArcanisFileSystem

fs = ArcanisFileSystem()

# Create some documents
fs.create_file("/docs/readme.md", b"# Project README")
fs.create_file("/docs/guide.md", b"## User Guide\nPython tutorial...")

# Index and search
fs.index_all()
results = fs.search("python tutorial")
for r in results:
    print(f"{r.path} (score: {r.score:.2f})")
```

## Best Practices

1. **Use context managers** for automatic cleanup:
   ```python
   with ArcanisFileSystem() as fs:
       # your code
   ```

2. **Enable AI features** when needed:
   ```python
   fs = ArcanisFileSystem(enable_ai=True)
   ```

3. **Create snapshots** before major changes:
   ```python
   fs.snapshot("before_migration")
   ```

4. **Run fsck** periodically:
   ```bash
   python tools/arcanis_fsck.py
   ```
