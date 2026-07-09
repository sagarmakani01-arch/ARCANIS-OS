"""Main ArcanisFileSystem class.

Integrates all subsystems: inodes, directories, permissions, metadata,
security, storage, and AI features into a unified filesystem interface.
"""

import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Dict, List, Optional, Tuple, Union

from core.inode import Inode, InodeTable, InodeType
from core.blocks import BlockAllocator
from core.directory import Directory, DirectoryTree, EntryType, DirectoryEntry
from core.metadata import MetadataManager, MetadataType
from permissions.posix import PosixPermissions
from permissions.acl import ACL, ACLEntry, ACLPermission, ACLScope
from permissions.auth import Authenticator, User, Session
from storage.backend import StorageBackend
from storage.memory import MemoryBackend
from security.encryption import EncryptionManager, EncryptionKey
from security.recovery import RecoveryManager, Snapshot, SnapshotType
from security.audit import AuditLogger, AuditEvent, AuditLevel
from ai.embeddings import EmbeddingEngine
from ai.indexer import AutoIndexer, IndexType
from ai.search import SemanticSearch, SearchQuery, SearchMode
from ai.organizer import SmartOrganizer


@dataclass
class FileHandle:
    """Open file handle for read/write operations."""

    inode: Inode
    mode: str = "r"
    position: int = 0
    handle_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    opened_at: float = field(default_factory=time.time)
    is_dirty: bool = False


class ArcanisFileSystem:
    """Unified filesystem interface for ArcanisOS."""

    VERSION = "1.0.0"
    BLOCK_SIZE = 4096
    MAX_PATH_LENGTH = 4096
    MAX_FILENAME_LENGTH = 255

    def __init__(self, storage_backend: Optional[StorageBackend] = None, mount_point: str = "/", enable_ai: bool = True):
        self.mount_point = mount_point
        self._storage = storage_backend or MemoryBackend(block_size=self.BLOCK_SIZE)

        self._inodes = InodeTable()
        self._blocks = BlockAllocator(total_blocks=self._storage.total_blocks if hasattr(self._storage, 'total_blocks') else 100000, block_size=self.BLOCK_SIZE)
        self._directories = DirectoryTree()
        self._metadata = MetadataManager()
        self._permissions = Authenticator()
        self._encryption = EncryptionManager()
        self._recovery = RecoveryManager()
        self._audit = AuditLogger()

        if enable_ai:
            self._embeddings = EmbeddingEngine()
            self._indexer = AutoIndexer()
            self._search_engine = SemanticSearch(self._embeddings, self._indexer)
            self._organizer = SmartOrganizer()
            self._organizer.create_default_rules()
        else:
            self._embeddings = None
            self._indexer = None
            self._search_engine = None
            self._organizer = None

        self._open_handles: Dict[str, FileHandle] = {}
        self._root_inode: Optional[uuid.UUID] = None
        self._mounted = False

        self._initialize_filesystem()

    def _initialize_filesystem(self) -> None:
        self._root_inode = self._create_root_directory()
        self._mounted = True
        self._audit.log(AuditEvent.SYSTEM_ERROR, AuditLevel.INFO, details={"action": "filesystem_initialized", "version": self.VERSION})

    def _create_root_directory(self) -> uuid.UUID:
        root_inode = self._inodes.allocate(InodeType.DIRECTORY, 0o755)
        root_inode.uid = 0
        root_inode.gid = 0
        self._directories.create_directory(root_inode.id)
        self._metadata.create(root_inode.id)
        return root_inode.id

    def _resolve_path(self, path: str) -> uuid.UUID:
        path = path.replace("\\", "/")
        if not path.startswith("/"):
            path = self.mount_point.rstrip("/") + "/" + path

        parts = [p for p in path.split("/") if p]
        current_id = self._root_inode

        for part in parts:
            if part == ".":
                continue
            if part == "..":
                directory = self._directories.get_directory(current_id)
                if directory and directory.parent_id:
                    current_id = directory.parent_id
                continue

            directory = self._directories.get_directory(current_id)
            if not directory:
                raise FileNotFoundError(f"Directory not found: {path}")

            entry = directory.get_entry(part)
            if not entry:
                raise FileNotFoundError(f"Path not found: {path}")

            current_id = entry.inode_id

        return current_id

    def _get_parent_and_name(self, path: str) -> Tuple[uuid.UUID, str]:
        path = path.rstrip("/")
        if "/" in path:
            parent_path = path[:path.rfind("/")]
            name = path[path.rfind("/") + 1:]
        else:
            parent_path = "/"
            name = path

        if not name:
            raise ValueError(f"Invalid path: {path}")

        parent_id = self._resolve_path(parent_path if parent_path else "/")
        return parent_id, name

    def _check_permission(self, inode: Inode, uid: int, gid: int, perm: str) -> bool:
        user = self._permissions.get_user(uid)
        if user and self._permissions.is_root(uid):
            return True

        perms = PosixPermissions(mode=inode.permissions)

        if perm == "read":
            return perms.check_read(uid, gid, inode.uid, inode.gid)
        elif perm == "write":
            return perms.check_write(uid, gid, inode.uid, inode.gid)
        elif perm == "execute":
            return perms.check_execute(uid, gid, inode.uid, inode.gid)
        return False

    def _get_current_user(self) -> User:
        users = self._permissions.list_users()
        for user in users:
            if user.id != 0 and user.id != 65534:
                return user
        return users[0] if users else self._permissions.get_user(0)

    def create_file(self, path: str, content: bytes = b"", permissions: int = 0o644, uid: Optional[int] = None, gid: Optional[int] = None) -> uuid.UUID:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        parent_id, name = self._get_parent_and_name(path)

        if len(name) > self.MAX_FILENAME_LENGTH:
            raise ValueError(f"Filename too long: {len(name)} > {self.MAX_FILENAME_LENGTH}")

        parent_inode = self._inodes.get(parent_id)
        if not parent_inode:
            raise FileNotFoundError("Parent directory not found")

        if not self._check_permission(parent_inode, uid, gid, "write"):
            raise PermissionError("Permission denied")

        parent_dir = self._directories.get_directory(parent_id)
        if parent_dir and parent_dir.has_entry(name):
            raise FileExistsError(f"File already exists: {path}")

        inode = self._inodes.allocate(InodeType.FILE, permissions)
        inode.uid = uid
        inode.gid = gid

        if content:
            inode.size = len(content)
            block_ids = self._blocks.allocate(inode.calculate_blocks_needed(self.BLOCK_SIZE))
            inode.block_pointers = block_ids

            offset = 0
            for block_id in block_ids:
                write_len = self._storage.write(block_id, content[offset:offset + self.BLOCK_SIZE])
                offset += write_len

        self._directories.get_directory(parent_id).add_entry(name, inode.id, EntryType.FILE)
        self._metadata.create(inode.id)

        if content and self._indexer:
            self._indexer.index_file(inode.id, path, content)
        if content and self._embeddings:
            metadata = {"name": name}
            self._embeddings.generate_embedding(inode.id, content, metadata)

        self._audit.log_file_operation(
            AuditEvent.FILE_CREATE, path, uid, user.username,
            details={"size": inode.size, "permissions": oct(permissions)}
        )

        return inode.id

    def read_file(self, path: str, uid: Optional[int] = None, gid: Optional[int] = None) -> bytes:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"File not found: {path}")

        if inode.inode_type != InodeType.FILE:
            raise IsADirectoryError(f"Not a file: {path}")

        if not self._check_permission(inode, uid, gid, "read"):
            raise PermissionError("Permission denied")

        inode.touch_access()
        self._metadata.touch_access(inode_id)

        data = b""
        for block_id in inode.block_pointers:
            block_data = self._storage.read(block_id)
            data += block_data[:min(self.BLOCK_SIZE, inode.size - len(data))]

        if inode.is_encrypted:
            data = self._encryption.decrypt_file_data(inode_id, data)

        self._audit.log_file_operation(
            AuditEvent.FILE_READ, path, uid, user.username,
            details={"size": len(data)}
        )

        return data[:inode.size]

    def write_file(self, path: str, content: bytes, uid: Optional[int] = None, gid: Optional[int] = None, append: bool = False) -> int:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"File not found: {path}")

        if inode.inode_type != InodeType.FILE:
            raise IsADirectoryError(f"Not a file: {path}")

        if not self._check_permission(inode, uid, gid, "write"):
            raise PermissionError("Permission denied")

        if inode.is_encrypted:
            content = self._encryption.encrypt_file_data(inode_id, content)

        if append:
            existing_data = b""
            for block_id in inode.block_pointers:
                block_data = self._storage.read(block_id)
                existing_data += block_data[:min(self.BLOCK_SIZE, inode.size - len(existing_data))]
            content = existing_data[:inode.size] + content

        if inode.block_pointers:
            self._blocks.free(inode.block_pointers)
            inode.block_pointers = []

        inode.size = len(content)
        new_blocks_needed = inode.calculate_blocks_needed(self.BLOCK_SIZE)

        if new_blocks_needed > len(inode.block_pointers):
            additional = new_blocks_needed - len(inode.block_pointers)
            new_block_ids = self._blocks.allocate(additional)
            inode.block_pointers.extend(new_block_ids)

        offset = 0
        for block_id in inode.block_pointers:
            if offset >= inode.size:
                break
            bytes_to_write = min(self.BLOCK_SIZE, inode.size - offset)
            self._storage.write(block_id, content[offset:offset + bytes_to_write])
            offset += bytes_to_write

        inode.touch_modify()
        self._metadata.touch_modify(inode_id)

        if self._indexer:
            full_content = self.read_file(path, uid, gid) if not append else content
            self._indexer.index_file(inode_id, path, full_content)

        self._audit.log_file_operation(
            AuditEvent.FILE_WRITE, path, uid, user.username,
            details={"bytes_written": len(content), "append": append}
        )

        return len(content)

    def delete_file(self, path: str, uid: Optional[int] = None, gid: Optional[int] = None) -> bool:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        parent_id, name = self._get_parent_and_name(path)
        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"File not found: {path}")

        if not self._check_permission(inode, uid, gid, "write"):
            raise PermissionError("Permission denied")

        if inode.block_pointers:
            self._blocks.free(inode.block_pointers)

        parent_dir = self._directories.get_directory(parent_id)
        if parent_dir:
            parent_dir.remove_entry(name)

        self._inodes.remove(inode_id)
        self._metadata.remove(inode_id)
        self._encryption.unassign_key(inode_id)

        if self._indexer:
            self._indexer.remove_index(inode_id)
        if self._embeddings:
            self._embeddings.remove_embedding(inode_id)

        self._audit.log_file_operation(
            AuditEvent.FILE_DELETE, path, uid, user.username
        )

        return True

    def create_directory(self, path: str, permissions: int = 0o755, uid: Optional[int] = None, gid: Optional[int] = None) -> uuid.UUID:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        parent_id, name = self._get_parent_and_name(path)

        parent_inode = self._inodes.get(parent_id)
        if not parent_inode:
            raise FileNotFoundError("Parent directory not found")

        if not self._check_permission(parent_inode, uid, gid, "write"):
            raise PermissionError("Permission denied")

        parent_dir = self._directories.get_directory(parent_id)
        if parent_dir and parent_dir.has_entry(name):
            raise FileExistsError(f"Directory already exists: {path}")

        inode = self._inodes.allocate(InodeType.DIRECTORY, permissions)
        inode.uid = uid
        inode.gid = gid

        new_dir = self._directories.create_directory(inode.id, parent_id)
        parent_dir.add_entry(name, inode.id, EntryType.DIRECTORY)
        self._metadata.create(inode.id)

        self._audit.log_file_operation(
            AuditEvent.DIR_CREATE, path, uid, user.username
        )

        return inode.id

    def list_directory(self, path: str, uid: Optional[int] = None, gid: Optional[int] = None) -> List[DirectoryEntry]:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"Directory not found: {path}")

        if inode.inode_type != InodeType.DIRECTORY:
            raise NotADirectoryError(f"Not a directory: {path}")

        if not self._check_permission(inode, uid, gid, "read"):
            raise PermissionError("Permission denied")

        directory = self._directories.get_directory(inode_id)
        return directory.list_entries() if directory else []

    def delete_directory(self, path: str, uid: Optional[int] = None, gid: Optional[int] = None) -> bool:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        parent_id, name = self._get_parent_and_name(path)
        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"Directory not found: {path}")

        if inode.inode_type != InodeType.DIRECTORY:
            raise NotADirectoryError(f"Not a directory: {path}")

        if not self._check_permission(inode, uid, gid, "write"):
            raise PermissionError("Permission denied")

        directory = self._directories.get_directory(inode_id)
        if directory and not directory.is_empty():
            raise OSError("Directory not empty")

        parent_dir = self._directories.get_directory(parent_id)
        if parent_dir:
            parent_dir.remove_entry(name)

        self._directories.remove_directory(inode_id)
        self._inodes.remove(inode_id)
        self._metadata.remove(inode_id)

        self._audit.log_file_operation(
            AuditEvent.DIR_DELETE, path, uid, user.username
        )

        return True

    def rename(self, old_path: str, new_path: str, uid: Optional[int] = None, gid: Optional[int] = None) -> bool:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        old_parent_id, old_name = self._get_parent_and_name(old_path)
        new_parent_id, new_name = self._get_parent_and_name(new_path)

        old_inode_id = self._resolve_path(old_path)
        old_inode = self._inodes.get(old_inode_id)

        if not old_inode:
            raise FileNotFoundError(f"Source not found: {old_path}")

        if not self._check_permission(old_inode, uid, gid, "write"):
            raise PermissionError("Permission denied")

        old_parent_dir = self._directories.get_directory(old_parent_id)
        new_parent_dir = self._directories.get_directory(new_parent_id)

        if new_parent_dir and new_parent_dir.has_entry(new_name):
            raise FileExistsError(f"Destination exists: {new_path}")

        if old_parent_id == new_parent_id:
            old_parent_dir.rename_entry(old_name, new_name)
        else:
            new_inode = self._inodes.get(old_inode_id)
            entry_type = EntryType.DIRECTORY if new_inode.inode_type == InodeType.DIRECTORY else EntryType.FILE

            old_parent_dir.remove_entry(old_name)
            new_parent_dir.add_entry(new_name, old_inode_id, entry_type)

            if new_inode.inode_type == InodeType.DIRECTORY:
                directory = self._directories.get_directory(old_inode_id)
                if directory:
                    directory.parent_id = new_parent_id

        self._audit.log(AuditEvent.FILE_RENAME, path=old_path, user_id=uid, username=user.username,
                       details={"old": old_path, "new": new_path})

        return True

    def chmod(self, path: str, mode: int, uid: Optional[int] = None, gid: Optional[int] = None) -> bool:
        user = self._get_current_user()
        uid = uid or user.id
        gid = gid or user.primary_group

        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"Not found: {path}")

        if inode.uid != uid and not self._permissions.is_root(uid):
            raise PermissionError("Only file owner or root can change permissions")

        inode.update_permissions(mode)
        self._audit.log(AuditEvent.FILE_CHMOD, path=path, user_id=uid, username=user.username,
                       details={"mode": oct(mode)})

        return True

    def stat(self, path: str) -> Dict:
        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"Not found: {path}")

        return inode.to_dict()

    def open_file(self, path: str, mode: str = "r") -> str:
        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            if "w" in mode or "a" in mode:
                inode_id = self.create_file(path)
                inode = self._inodes.get(inode_id)
            else:
                raise FileNotFoundError(f"File not found: {path}")

        handle = FileHandle(inode=inode, mode=mode)
        self._open_handles[handle.handle_id] = handle
        return handle.handle_id

    def close_file(self, handle_id: str) -> None:
        handle = self._open_handles.pop(handle_id, None)
        if handle and handle.is_dirty:
            handle.inode.touch_modify()

    def encrypt_file(self, path: str, uid: Optional[int] = None) -> bool:
        user = self._get_current_user()
        uid = uid or user.id

        inode_id = self._resolve_path(path)
        inode = self._inodes.get(inode_id)

        if not inode:
            raise FileNotFoundError(f"File not found: {path}")

        if not self._check_permission(inode, uid, user.primary_group, "write"):
            raise PermissionError("Permission denied")

        content = self.read_file(path, uid)
        encrypted = self._encryption.encrypt_file_data(inode_id, content)

        if inode.block_pointers:
            self._blocks.free(inode.block_pointers)

        inode.size = len(encrypted)
        block_ids = self._blocks.allocate(inode.calculate_blocks_needed(self.BLOCK_SIZE))
        inode.block_pointers = block_ids

        offset = 0
        for block_id in block_ids:
            self._storage.write(block_id, encrypted[offset:offset + self.BLOCK_SIZE])
            offset += self.BLOCK_SIZE

        inode.is_encrypted = True
        inode.touch_modify()

        self._audit.log(AuditEvent.FILE_ENCRYPT, path=path, uid=uid, username=user.username)

        return True

    def snapshot(self, name: str = "", snapshot_type: SnapshotType = SnapshotType.FULL) -> Snapshot:
        snap = self._recovery.create_snapshot(name, snapshot_type)

        inodes = [str(i.id) for i in self._inodes.all_inodes()]
        self._recovery.complete_snapshot(snap.id, self._inodes.total_size(), inodes)

        self._audit.log(AuditEvent.SNAPSHOT_CREATE, details={"snapshot_id": snap.id, "name": name})

        return snap

    def search(self, query: str, mode: SearchMode = SearchMode.HYBRID, max_results: int = 50) -> list:
        if not self._search_engine:
            return []

        search_query = SearchQuery(text=query, mode=mode, max_results=max_results)
        return self._search_engine.search(search_query)

    def index_all(self) -> int:
        if not self._indexer:
            return 0

        count = 0
        for inode in self._inodes.find_by_type(InodeType.FILE):
            content = b""
            for block_id in inode.block_pointers:
                content += self._storage.read(block_id)[:min(self.BLOCK_SIZE, inode.size - len(content))]

            path = self._directories.get_path(inode.id)
            self._indexer.index_file(inode.id, path, content[:inode.size])

            if self._embeddings:
                self._embeddings.generate_embedding(inode.id, content[:inode.size])

            count += 1

        return count

    def get_info(self) -> dict:
        return {
            "version": self.VERSION,
            "mount_point": self.mount_point,
            "mounted": self._mounted,
            "block_size": self.BLOCK_SIZE,
            "total_inodes": self._inodes.count(),
            "total_files": len(self._inodes.find_by_type(InodeType.FILE)),
            "total_directories": len(self._inodes.find_by_type(InodeType.DIRECTORY)),
            "total_size": self._inodes.total_size(),
            "total_blocks": self._inodes.total_blocks(),
            "open_handles": len(self._open_handles),
            "storage": self._storage.get_info() if hasattr(self._storage, 'get_info') else {},
            "encryption_keys": len(self._encryption.list_keys()),
            "snapshots": len(self._recovery.list_snapshots()),
            "audit_entries": self._audit.get_info()["total_entries"],
            "ai_enabled": self._embeddings is not None,
        }

    def sync(self) -> None:
        if hasattr(self._storage, 'sync'):
            self._storage.sync()

    def unmount(self) -> None:
        for handle_id in list(self._open_handles.keys()):
            self.close_file(handle_id)
        self.sync()
        self._mounted = False
        self._audit.log(AuditEvent.SYSTEM_ERROR, AuditLevel.INFO, details={"action": "filesystem_unmounted"})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unmount()
        return False
