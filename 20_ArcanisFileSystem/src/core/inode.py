"""Inode system for ArcanisFileSystem.

Each file/directory is represented by an inode containing:
- File type and permissions
- Size and block pointers
- Timestamps (creation, modification, access)
- Reference count
"""

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional


class InodeType(enum.IntEnum):
    FILE = 0
    DIRECTORY = 1
    SYMLINK = 2
    DEVICE = 3
    SOCKET = 4
    PIPE = 5


@dataclass
class Inode:
    """Represents an inode in the filesystem."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    inode_type: InodeType = InodeType.FILE
    size: int = 0
    permissions: int = 0o644
    uid: int = 0
    gid: int = 0
    block_pointers: List[int] = field(default_factory=list)
    indirect_block: Optional[int] = None
    double_indirect_block: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    reference_count: int = 1
    extended_attrs: dict = field(default_factory=dict)
    is_encrypted: bool = False
    encryption_key_id: Optional[str] = None

    def touch_access(self) -> None:
        self.accessed_at = time.time()

    def touch_modify(self) -> None:
        self.modified_at = time.time()

    def calculate_blocks_needed(self, block_size: int = 4096) -> int:
        if self.size == 0:
            return 0
        return (self.size + block_size - 1) // block_size

    def get_direct_block_count(self) -> int:
        return min(len(self.block_pointers), 12)

    def get_total_blocks(self) -> int:
        return len(self.block_pointers)

    def update_permissions(self, mode: int) -> None:
        self.permissions = mode & 0o7777
        self.touch_modify()

    def set_extended_attr(self, key: str, value) -> None:
        self.extended_attrs[key] = value
        self.touch_modify()

    def get_extended_attr(self, key: str, default=None):
        return self.extended_attrs.get(key, default)

    def remove_extended_attr(self, key: str) -> bool:
        if key in self.extended_attrs:
            del self.extended_attrs[key]
            self.touch_modify()
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "type": self.inode_type.name,
            "size": self.size,
            "permissions": oct(self.permissions),
            "uid": self.uid,
            "gid": self.gid,
            "blocks": self.get_total_blocks(),
            "created": self.created_at,
            "modified": self.modified_at,
            "accessed": self.accessed_at,
            "refs": self.reference_count,
            "encrypted": self.is_encrypted,
        }


class InodeTable:
    """Manages the collection of all inodes."""

    def __init__(self):
        self._inodes: dict = {}

    def allocate(self, inode_type: InodeType = InodeType.FILE, permissions: int = 0o644) -> Inode:
        inode = Inode(inode_type=inode_type, permissions=permissions)
        self._inodes[inode.id] = inode
        return inode

    def get(self, inode_id: uuid.UUID) -> Optional[Inode]:
        return self._inodes.get(inode_id)

    def remove(self, inode_id: uuid.UUID) -> bool:
        if inode_id in self._inodes:
            del self._inodes[inode_id]
            return True
        return False

    def exists(self, inode_id: uuid.UUID) -> bool:
        return inode_id in self._inodes

    def count(self) -> int:
        return len(self._inodes)

    def all_ids(self) -> List[uuid.UUID]:
        return list(self._inodes.keys())

    def all_inodes(self) -> List[Inode]:
        return list(self._inodes.values())

    def find_by_type(self, inode_type: InodeType) -> List[Inode]:
        return [i for i in self._inodes.values() if i.inode_type == inode_type]

    def find_by_owner(self, uid: int) -> List[Inode]:
        return [i for i in self._inodes.values() if i.uid == uid]

    def total_size(self) -> int:
        return sum(i.size for i in self._inodes.values())

    def total_blocks(self) -> int:
        return sum(i.get_total_blocks() for i in self._inodes.values())

    def clear(self) -> None:
        self._inodes.clear()
