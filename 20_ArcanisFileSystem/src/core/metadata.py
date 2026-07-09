"""Metadata management for ArcanisFileSystem.

Stores and manages extended metadata for files and directories.
Supports custom metadata fields and automatic tracking.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MetadataType(Enum):
    STANDARD = "standard"
    CUSTOM = "custom"
    AI_GENERATED = "ai_generated"
    SYSTEM = "system"


@dataclass
class MetadataField:
    """Represents a single metadata field."""

    key: str
    value: Any
    metadata_type: MetadataType = MetadataType.CUSTOM
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    immutable: bool = False

    def update(self, new_value: Any) -> None:
        if self.immutable:
            raise ValueError(f"Metadata field '{self.key}' is immutable")
        self.value = new_value
        self.updated_at = time.time()

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "type": self.metadata_type.value,
            "created": self.created_at,
            "updated": self.updated_at,
            "immutable": self.immutable,
        }


@dataclass
class FileMetadata:
    """Complete metadata for a single file/directory."""

    inode_id: uuid.UUID
    fields: Dict[str, MetadataField] = field(default_factory=dict)

    def set(self, key: str, value: Any, metadata_type: MetadataType = MetadataType.CUSTOM, immutable: bool = False) -> None:
        if key in self.fields and self.fields[key].immutable:
            raise ValueError(f"Metadata field '{key}' is immutable")

        self.fields[key] = MetadataField(
            key=key,
            value=value,
            metadata_type=metadata_type,
            immutable=immutable,
        )

    def get(self, key: str, default: Any = None) -> Any:
        field = self.fields.get(key)
        return field.value if field else default

    def remove(self, key: str) -> bool:
        field = self.fields.get(key)
        if field and not field.immutable:
            del self.fields[key]
            return True
        return False

    def has(self, key: str) -> bool:
        return key in self.fields

    def keys(self) -> List[str]:
        return list(self.fields.keys())

    def values(self) -> List[Any]:
        return [f.value for f in self.fields.values()]

    def items(self) -> List[tuple]:
        return [(f.key, f.value) for f in self.fields.values()]

    def count(self) -> int:
        return len(self.fields)

    def clear(self) -> None:
        immutable_fields = {k: v for k, v in self.fields.items() if v.immutable}
        self.fields.clear()
        self.fields.update(immutable_fields)

    def to_dict(self) -> dict:
        return {key: field.to_dict() for key, field in self.fields.items()}

    def calculate_size(self) -> int:
        import sys
        return sys.getsizeof(self.fields)


class MetadataManager:
    """Manages metadata for all files in the filesystem."""

    STANDARD_FIELDS = [
        "mime_type", "encoding", "language", "tags",
        "description", "author", "version", "checksum",
    ]

    def __init__(self):
        self._metadata: Dict[uuid.UUID, FileMetadata] = {}

    def create(self, inode_id: uuid.UUID) -> FileMetadata:
        if inode_id in self._metadata:
            raise ValueError(f"Metadata for inode {inode_id} already exists")

        metadata = FileMetadata(inode_id=inode_id)
        self._metadata[inode_id] = metadata

        metadata.set("created_at", time.time(), MetadataType.STANDARD, immutable=True)
        metadata.set("modified_at", time.time(), MetadataType.STANDARD)
        metadata.set("accessed_at", time.time(), MetadataType.STANDARD)

        return metadata

    def get(self, inode_id: uuid.UUID) -> Optional[FileMetadata]:
        return self._metadata.get(inode_id)

    def remove(self, inode_id: uuid.UUID) -> bool:
        if inode_id in self._metadata:
            del self._metadata[inode_id]
            return True
        return False

    def exists(self, inode_id: uuid.UUID) -> bool:
        return inode_id in self._metadata

    def set_field(self, inode_id: uuid.UUID, key: str, value: Any, metadata_type: MetadataType = MetadataType.CUSTOM) -> None:
        metadata = self._metadata.get(inode_id)
        if not metadata:
            metadata = self.create(inode_id)
        metadata.set(key, value, metadata_type)

    def get_field(self, inode_id: uuid.UUID, key: str, default: Any = None) -> Any:
        metadata = self._metadata.get(inode_id)
        if metadata:
            return metadata.get(key, default)
        return default

    def touch_access(self, inode_id: uuid.UUID) -> None:
        metadata = self._metadata.get(inode_id)
        if metadata:
            metadata.set("accessed_at", time.time(), MetadataType.STANDARD)

    def touch_modify(self, inode_id: uuid.UUID) -> None:
        metadata = self._metadata.get(inode_id)
        if metadata:
            metadata.set("modified_at", time.time(), MetadataType.STANDARD)

    def search_by_field(self, key: str, value: Any) -> List[uuid.UUID]:
        results = []
        for inode_id, metadata in self._metadata.items():
            if metadata.get(key) == value:
                results.append(inode_id)
        return results

    def search_by_type(self, metadata_type: MetadataType) -> List[uuid.UUID]:
        results = []
        for inode_id, metadata in self._metadata.items():
            for field in metadata.fields.values():
                if field.metadata_type == metadata_type:
                    results.append(inode_id)
                    break
        return results

    def copy_metadata(self, source_id: uuid.UUID, target_id: uuid.UUID) -> Optional[FileMetadata]:
        source = self._metadata.get(source_id)
        if not source:
            return None

        target = self.create(target_id)
        for key, field in source.fields.items():
            if not field.immutable:
                target.set(key, field.value, field.metadata_type)

        return target

    def get_all_metadata(self, inode_id: uuid.UUID) -> dict:
        metadata = self._metadata.get(inode_id)
        if metadata:
            return metadata.to_dict()
        return {}

    def total_entries(self) -> int:
        return sum(m.count() for m in self._metadata.values())

    def clear(self) -> None:
        self._metadata.clear()
