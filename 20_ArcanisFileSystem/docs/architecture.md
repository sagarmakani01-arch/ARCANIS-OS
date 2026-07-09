# ArcanisFileSystem Architecture

## Overview

ArcanisFileSystem is a modular, modern filesystem designed for ArcanisOS. It combines traditional filesystem concepts with AI-powered features for intelligent file management.

## Core Components

### 1. Inode System (`core/inode.py`)
- Each file/directory represented by an inode
- Supports file types: FILE, DIRECTORY, SYMLINK, DEVICE, SOCKET, PIPE
- Stores permissions, timestamps, block pointers, extended attributes
- UUID-based identification for distributed systems

### 2. Block Allocator (`core/blocks.py`)
- Manages storage block allocation
- Supports direct, indirect, and double-indirect pointers
- Free-space bitmap for efficient allocation
- Configurable block size (default: 4096 bytes)

### 3. Directory Structure (`core/directory.py`)
- Hierarchical tree structure
- B-tree-like lookups for O(log n) access
- Path resolution and parent tracking
- Entry types: FILE, DIRECTORY, SYMLINK

### 4. Metadata Manager (`core/metadata.py`)
- Extended metadata for files
- Standard fields: mime_type, tags, description
- Custom fields support
- Automatic timestamp tracking

## Permission System

### POSIX Permissions (`permissions/posix.py`)
- Standard Unix permission bits (rwxrwxrwx)
- SetUID, SetGID, sticky bit support
- Owner/group/other permission checks

### Access Control Lists (`permissions/acl.py`)
- Fine-grained permission control
- Named users and groups
- Inheritance for directories
- Permission grant/revoke operations

### Authentication (`permissions/auth.py`)
- User management with PBKDF2 password hashing
- Session management with expiry
- Group membership tracking

## Security Layer

### Encryption (`security/encryption.py`)
- AES-256-GCM encryption for data at rest
- Key management with rotation support
- Per-file encryption key assignment
- Salt-based key derivation

### Recovery (`security/recovery.py`)
- Snapshot-based recovery system
- Full, incremental, and differential snapshots
- Snapshot chain tracking
- Integrity verification

### Audit Logging (`security/audit.py`)
- Comprehensive operation logging
- Query and filtering capabilities
- Event callbacks for real-time monitoring
- Export to JSON format

## AI Features

### Embeddings (`ai/embeddings.py`)
- TF-IDF based text embeddings
- Cosine similarity search
- Vocabulary building and IDF scoring
- Content and metadata feature extraction

### Auto-Indexer (`ai/indexer.py`)
- Automatic keyword extraction
- Tag-based indexing
- MIME type classification
- Reindexing detection

### Semantic Search (`ai/search.py`)
- Hybrid search (keyword + semantic)
- Fuzzy matching with Levenshtein distance
- Regex pattern matching
- Query suggestions and history

### Smart Organizer (`ai/organizer.py`)
- Rule-based file organization
- Multiple match conditions
- Configurable actions (move, copy, tag, etc.)
- Priority-based rule execution

## Storage Backends

### Memory Backend (`storage/memory.py`)
- In-memory block storage
- Fast allocation and deallocation
- Ideal for testing and ephemeral filesystems

### Disk Backend (`storage/disk.py`)
- Persistent storage to disk
- JSON-based index persistence
- Data integrity with fsync
- Configurable block and total sizes

## Main Filesystem (`core/filesystem.py`)

The `ArcanisFileSystem` class integrates all subsystems:
- Unified API for file operations
- Permission checking
- Encryption support
- AI feature integration
- Audit logging
- Snapshot creation

## Design Decisions

1. **UUID-based inodes**: Enables distributed filesystem support
2. **Modular architecture**: Each component is independent and testable
3. **Pure Python**: No external dependencies for maximum portability
4. **AI integration**: Optional AI features don't impact core performance
5. **Security-first**: Encryption, ACLs, and audit logging built-in
