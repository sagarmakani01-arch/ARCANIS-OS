# ArcanisFileSystem API Reference

## Core FileSystem

### ArcanisFileSystem

```python
from core.filesystem import ArcanisFileSystem

fs = ArcanisFileSystem(
    storage_backend=None,  # StorageBackend instance
    mount_point="/",       # Mount point path
    enable_ai=True         # Enable AI features
)
```

#### File Operations

```python
# Create file
inode_id = fs.create_file("/path/file.txt", b"content", permissions=0o644)

# Read file
content = fs.read_file("/path/file.txt")

# Write file (overwrite)
bytes_written = fs.write_file("/path/file.txt", b"new content")

# Append to file
bytes_written = fs.write_file("/path/file.txt", b" more", append=True)

# Delete file
success = fs.delete_file("/path/file.txt")

# Rename/move
success = fs.rename("/old/path.txt", "/new/path.txt")

# Get file info
info = fs.stat("/path/file.txt")
```

#### Directory Operations

```python
# Create directory
inode_id = fs.create_directory("/documents", permissions=0o755)

# List directory
entries = fs.list_directory("/documents")
# Returns: List[DirectoryEntry]

# Delete empty directory
success = fs.delete_directory("/empty_dir")
```

#### Permission Operations

```python
# Change permissions
fs.chmod("/path/file.txt", 0o755)
```

#### Encryption

```python
# Encrypt file
fs.encrypt_file("/path/file.txt")
```

#### Snapshots

```python
# Create snapshot
snapshot = fs.snapshot("backup_name")
```

#### Search (AI)

```python
# Search files
results = fs.search("query text")
```

#### System

```python
# Get filesystem info
info = fs.get_info()

# Sync to disk
fs.sync()

# Unmount
fs.unmount()

# Context manager
with ArcanisFileSystem() as fs:
    fs.create_file("/test.txt", b"data")
```

---

## Storage Backends

### MemoryBackend

```python
from storage.memory import MemoryBackend

backend = MemoryBackend(block_size=4096, total_blocks=100000)
```

### DiskBackend

```python
from storage.disk import DiskBackend

backend = DiskBackend(path="/path/to/storage", block_size=4096)
```

---

## Permissions

### PosixPermissions

```python
from permissions.posix import PosixPermissions

perms = PosixPermissions(0o755)
print(perms.to_symbolic())  # "rwxr-xr-x"
```

### ACL

```python
from permissions.acl import ACL, ACLEntry, ACLPermission, ACLScope

acl = ACL()
entry = ACLEntry(
    scope=ACLScope.EVERYONE,
    permissions=ACLPermission.READ
)
acl.add_entry(entry)
```

### Authenticator

```python
from permissions.auth import Authenticator

auth = Authenticator()
user = auth.create_user("john", "password123")
session = auth.create_session(user)
```

---

## Security

### EncryptionManager

```python
from security.encryption import EncryptionManager

em = EncryptionManager()
key = em.generate_key("my key")
encrypted = em.encrypt_block(b"data", key)
decrypted = em.decrypt_block(encrypted, key)
```

### RecoveryManager

```python
from security.recovery import RecoveryManager

rm = RecoveryManager()
snap = rm.create_snapshot("backup")
rm.complete_snapshot(snap.id, size=1024, inodes=["inode1"])
```

### AuditLogger

```python
from security.audit import AuditLogger, AuditEvent

al = AuditLogger()
al.log(AuditEvent.FILE_CREATE, path="/file.txt")
results = al.query(event=AuditEvent.FILE_CREATE)
```

---

## AI Features

### EmbeddingEngine

```python
from ai.embeddings import EmbeddingEngine

engine = EmbeddingEngine()
embedding = engine.generate_embedding(inode_id, content)
similar = engine.find_similar(embedding.vector, top_k=10)
```

### AutoIndexer

```python
from ai.indexer import AutoIndexer

indexer = AutoIndexer()
indexer.index_file(inode_id, "/path/file.txt", content)
results = indexer.search_keywords(["python"])
```

### SemanticSearch

```python
from ai.search import SemanticSearch, SearchQuery, SearchMode

search = SemanticSearch(indexer=indexer)
query = SearchQuery(text="python tutorial", mode=SearchMode.HYBRID)
results = search.search(query)
```

### SmartOrganizer

```python
from ai.organizer import SmartOrganizer, OrganizationRule, OrganizeAction, MatchCondition

organizer = SmartOrganizer()
rule = OrganizationRule(
    name="Images",
    conditions=[(MatchCondition.EXTENSION, "jpg")],
    action=OrganizeAction.MOVE,
    target_path="/Images/{name}{ext}"
)
organizer.add_rule(rule)
```
