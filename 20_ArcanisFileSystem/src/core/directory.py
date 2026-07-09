"""Directory structure for ArcanisFileSystem.

Implements a hierarchical directory tree using B-tree like structure
for efficient lookups and ordered entries.
"""

import enum
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class EntryType(enum.IntEnum):
    FILE = 0
    DIRECTORY = 1
    SYMLINK = 2


@dataclass
class DirectoryEntry:
    """Represents a single entry in a directory."""

    name: str
    inode_id: uuid.UUID
    entry_type: EntryType = EntryType.FILE

    def __repr__(self):
        return f"<DirEntry '{self.name}' [{self.entry_type.name}]>"


@dataclass
class Directory:
    """Represents a directory containing entries."""

    inode_id: uuid.UUID
    entries: Dict[str, DirectoryEntry] = field(default_factory=dict)
    parent_id: Optional[uuid.UUID] = None

    def add_entry(self, name: str, inode_id: uuid.UUID, entry_type: EntryType = EntryType.FILE) -> DirectoryEntry:
        if name in self.entries:
            raise FileExistsError(f"Entry '{name}' already exists in directory")

        if not self._is_valid_name(name):
            raise ValueError(f"Invalid entry name: '{name}'")

        entry = DirectoryEntry(name=name, inode_id=inode_id, entry_type=entry_type)
        self.entries[name] = entry
        return entry

    def remove_entry(self, name: str) -> Optional[DirectoryEntry]:
        return self.entries.pop(name, None)

    def get_entry(self, name: str) -> Optional[DirectoryEntry]:
        return self.entries.get(name)

    def rename_entry(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.entries:
            return False
        if new_name in self.entries:
            raise FileExistsError(f"Entry '{new_name}' already exists")

        if not self._is_valid_name(new_name):
            raise ValueError(f"Invalid entry name: '{new_name}'")

        entry = self.entries.pop(old_name)
        entry.name = new_name
        self.entries[new_name] = entry
        return True

    def list_entries(self, sort: bool = True) -> List[DirectoryEntry]:
        entries = list(self.entries.values())
        if sort:
            entries.sort(key=lambda e: e.name.lower())
        return entries

    def list_names(self, sort: bool = True) -> List[str]:
        return [e.name for e in self.list_entries(sort)]

    def find_entry(self, name: str) -> Optional[DirectoryEntry]:
        return self.entries.get(name)

    def entry_count(self) -> int:
        return len(self.entries)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def has_entry(self, name: str) -> bool:
        return name in self.entries

    def entries_by_type(self, entry_type: EntryType) -> List[DirectoryEntry]:
        return [e for e in self.entries.values() if e.entry_type == entry_type]

    def files(self) -> List[DirectoryEntry]:
        return self.entries_by_type(EntryType.FILE)

    def subdirectories(self) -> List[DirectoryEntry]:
        return self.entries_by_type(EntryType.DIRECTORY)

    def symlinks(self) -> List[DirectoryEntry]:
        return self.entries_by_type(EntryType.SYMLINK)

    @staticmethod
    def _is_valid_name(name: str) -> bool:
        if not name or name in (".", ".."):
            return False
        if "/" in name or "\\" in name:
            return False
        if len(name) > 255:
            return False
        return True

    def calculate_size(self) -> int:
        return sum(len(e.name.encode("utf-8")) + 16 for e in self.entries.values())


class DirectoryTree:
    """Manages the entire directory hierarchy."""

    def __init__(self):
        self._directories: Dict[uuid.UUID, Directory] = {}

    def create_directory(self, inode_id: uuid.UUID, parent_id: Optional[uuid.UUID] = None) -> Directory:
        if inode_id in self._directories:
            raise ValueError(f"Directory for inode {inode_id} already exists")

        directory = Directory(inode_id=inode_id, parent_id=parent_id)
        self._directories[inode_id] = directory
        return directory

    def get_directory(self, inode_id: uuid.UUID) -> Optional[Directory]:
        return self._directories.get(inode_id)

    def remove_directory(self, inode_id: uuid.UUID) -> bool:
        if inode_id in self._directories:
            directory = self._directories[inode_id]
            if not directory.is_empty():
                raise OSError("Cannot remove non-empty directory")
            del self._directories[inode_id]
            return True
        return False

    def get_parent(self, inode_id: uuid.UUID) -> Optional[Directory]:
        directory = self._directories.get(inode_id)
        if directory and directory.parent_id:
            return self._directories.get(directory.parent_id)
        return None

    def get_children(self, inode_id: uuid.UUID) -> List[Directory]:
        directory = self._directories.get(inode_id)
        if not directory:
            return []

        children = []
        for entry in directory.subdirectories():
            child = self._directories.get(entry.inode_id)
            if child:
                children.append(child)
        return children

    def resolve_path(self, root_inode_id: uuid.UUID, path: str) -> Optional[uuid.UUID]:
        parts = [p for p in path.replace("\\", "/").split("/") if p]
        current_id = root_inode_id

        for part in parts:
            directory = self._directories.get(current_id)
            if not directory:
                return None

            entry = directory.get_entry(part)
            if not entry:
                return None

            if part != parts[-1] and entry.entry_type != EntryType.DIRECTORY:
                return None

            current_id = entry.inode_id

        return current_id

    def get_path(self, target_inode_id: uuid.UUID) -> str:
        parts = []
        current_id = target_inode_id

        while current_id:
            directory = self._directories.get(current_id)
            if not directory or not directory.parent_id:
                break

            parent = self._directories.get(directory.parent_id)
            if not parent:
                break

            for entry in parent.list_entries():
                if entry.inode_id == current_id:
                    parts.append(entry.name)
                    break

            current_id = directory.parent_id

        parts.reverse()
        return "/" + "/".join(parts) if parts else "/"

    def count_entries(self) -> int:
        return sum(d.entry_count() for d in self._directories.values())

    def clear(self) -> None:
        self._directories.clear()
