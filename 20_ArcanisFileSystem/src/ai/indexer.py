"""Auto-indexing system for ArcanisFileSystem.

Automatically indexes file content and metadata for fast retrieval.
"""

import hashlib
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Set


class IndexType(Enum):
    CONTENT = "content"
    METADATA = "metadata"
    NAME = "name"
    PATH = "path"
    TAGS = "tags"
    FULL = "full"


@dataclass
class IndexEntry:
    """Represents a single indexed file."""

    inode_id: uuid.UUID
    path: str
    index_type: IndexType = IndexType.FULL
    indexed_at: float = field(default_factory=time.time)
    content_hash: str = ""
    keywords: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    size: int = 0
    mime_type: str = ""
    custom_fields: Dict[str, str] = field(default_factory=dict)

    def needs_reindex(self, content_hash: str) -> bool:
        return self.content_hash != content_hash

    def to_dict(self) -> dict:
        return {
            "inode_id": str(self.inode_id),
            "path": self.path,
            "index_type": self.index_type.value,
            "indexed_at": self.indexed_at,
            "content_hash": self.content_hash,
            "keywords_count": len(self.keywords),
            "tags": list(self.tags),
            "size": self.size,
        }


class AutoIndexer:
    """Automatically indexes files for search and organization."""

    MAX_INDEX_SIZE = 1000000
    BATCH_SIZE = 100

    def __init__(self):
        self._entries: Dict[uuid.UUID, IndexEntry] = {}
        self._path_index: Dict[str, uuid.UUID] = {}
        self._tag_index: Dict[str, Set[uuid.UUID]] = defaultdict(set)
        self._keyword_index: Dict[str, Set[uuid.UUID]] = defaultdict(set)
        self._mime_index: Dict[str, Set[uuid.UUID]] = defaultdict(set)
        self._callbacks: List[Callable[[IndexEntry], None]] = []
        self._total_indexed = 0

    def index_file(self, inode_id: uuid.UUID, path: str, content: bytes = b"", metadata: Optional[Dict] = None, index_type: IndexType = IndexType.FULL) -> IndexEntry:
        content_hash = hashlib.sha256(content).hexdigest()[:16]

        existing = self._entries.get(inode_id)
        if existing and not existing.needs_reindex(content_hash):
            return existing

        keywords = self._extract_keywords(content, metadata)
        tags = self._extract_tags(metadata)
        mime_type = metadata.get("mime_type", "application/octet-stream") if metadata else "application/octet-stream"

        entry = IndexEntry(
            inode_id=inode_id,
            path=path,
            index_type=index_type,
            content_hash=content_hash,
            keywords=keywords,
            tags=tags,
            size=len(content),
            mime_type=mime_type,
        )

        self._entries[inode_id] = entry
        self._path_index[path] = inode_id
        self._mime_index[mime_type].add(inode_id)

        for tag in tags:
            self._tag_index[tag].add(inode_id)

        for keyword in keywords:
            self._keyword_index[keyword].add(inode_id)

        self._total_indexed += 1

        for callback in self._callbacks:
            try:
                callback(entry)
            except Exception:
                pass

        return entry

    def remove_index(self, inode_id: uuid.UUID) -> bool:
        entry = self._entries.pop(inode_id, None)
        if not entry:
            return False

        self._path_index.pop(entry.path, None)
        self._mime_index.get(entry.mime_type, set()).discard(inode_id)

        for tag in entry.tags:
            self._tag_index[tag].discard(inode_id)

        for keyword in entry.keywords:
            self._keyword_index[keyword].discard(inode_id)

        return True

    def get_entry(self, inode_id: uuid.UUID) -> Optional[IndexEntry]:
        return self._entries.get(inode_id)

    def get_by_path(self, path: str) -> Optional[IndexEntry]:
        inode_id = self._path_index.get(path)
        if inode_id:
            return self._entries.get(inode_id)
        return None

    def search_keywords(self, keywords: List[str], match_all: bool = False) -> List[IndexEntry]:
        if not keywords:
            return []

        if match_all:
            matching_ids = None
            for keyword in keywords:
                keyword_lower = keyword.lower()
                ids = self._keyword_index.get(keyword_lower, set())
                if matching_ids is None:
                    matching_ids = ids.copy()
                else:
                    matching_ids &= ids
        else:
            matching_ids = set()
            for keyword in keywords:
                keyword_lower = keyword.lower()
                matching_ids |= self._keyword_index.get(keyword_lower, set())

        return [self._entries[inode_id] for inode_id in matching_ids if inode_id in self._entries]

    def search_by_tag(self, tag: str) -> List[IndexEntry]:
        tag_lower = tag.lower()
        inode_ids = self._tag_index.get(tag_lower, set())
        return [self._entries[inode_id] for inode_id in inode_ids if inode_id in self._entries]

    def search_by_mime(self, mime_type: str) -> List[IndexEntry]:
        inode_ids = self._mime_index.get(mime_type, set())
        return [self._entries[inode_id] for inode_id in inode_ids if inode_id in self._entries]

    def search_by_path_pattern(self, pattern: str) -> List[IndexEntry]:
        import fnmatch
        return [entry for entry in self._entries.values()
                if fnmatch.fnmatch(entry.path, pattern)]

    def get_all_entries(self) -> List[IndexEntry]:
        return list(self._entries.values())

    def add_callback(self, callback: Callable[[IndexEntry], None]) -> None:
        self._callbacks.append(callback)

    def needs_reindex(self, inode_id: uuid.UUID, content_hash: str) -> bool:
        entry = self._entries.get(inode_id)
        if not entry:
            return True
        return entry.needs_reindex(content_hash)

    def get_statistics(self) -> Dict[str, int]:
        stats = {
            "total_entries": len(self._entries),
            "total_keywords": len(self._keyword_index),
            "total_tags": len(self._tag_index),
            "total_mime_types": len(self._mime_index),
        }
        return stats

    def _extract_keywords(self, content: bytes, metadata: Optional[Dict] = None) -> List[str]:
        import re

        text = ""
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            pass

        if metadata:
            for key in ["name", "description", "tags", "author"]:
                if key in metadata:
                    text += f" {metadata[key]}"

        words = re.findall(r"[a-z0-9]+", text.lower())
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                       "have", "has", "had", "do", "does", "did", "will", "would", "could",
                       "should", "may", "might", "must", "shall", "can", "need", "dare",
                       "to", "of", "in", "for", "on", "with", "at", "by", "from", "as"}

        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:100]

    def _extract_tags(self, metadata: Optional[Dict] = None) -> Set[str]:
        tags = set()
        if metadata and "tags" in metadata:
            raw_tags = metadata["tags"]
            if isinstance(raw_tags, str):
                tags = {t.strip().lower() for t in raw_tags.split(",") if t.strip()}
            elif isinstance(raw_tags, list):
                tags = {t.strip().lower() for t in raw_tags if t}
        return tags

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        self._path_index.clear()
        self._tag_index.clear()
        self._keyword_index.clear()
        self._mime_index.clear()
        return count
