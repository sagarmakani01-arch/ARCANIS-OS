"""Disk-based storage backend for ArcanisFileSystem.

Persists filesystem data to disk for production use.
"""

import json
import os
import struct
from pathlib import Path
from typing import Dict, List, Optional, Set
from .backend import StorageBackend


class DiskBackend(StorageBackend):
    """Disk-based block storage backend."""

    MAGIC = b"ARCS"
    VERSION = 1
    HEADER_SIZE = 4096

    def __init__(self, path: str, block_size: int = 4096, total_blocks: int = 1048576):
        self.path = Path(path)
        self.block_size = block_size
        self.total_blocks = total_blocks
        self._data_file: Optional[open] = None
        self._index_file: Optional[open] = None
        self._free_blocks: Set[int] = set()
        self._used_blocks: Set[int] = set()
        self._sync_count = 0
        self._initialized = False

        self._initialize()

    def _initialize(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)

        data_path = self.path / "blocks.dat"
        index_path = self.path / "index.json"

        if data_path.exists() and index_path.exists():
            self._load_index()
        else:
            self._create_new()

        self._data_file = open(data_path, "r+b" if data_path.exists() else "w+b")
        self._initialized = True

    def _create_new(self) -> None:
        data_path = self.path / "blocks.dat"
        index_path = self.path / "index.json"

        with open(data_path, "wb") as f:
            header = self._create_header()
            f.write(header)
            f.write(b"\x00" * (self.block_size - len(header)))

        self._free_blocks = set(range(self.total_blocks))
        self._used_blocks = set()
        self._save_index()

    def _create_header(self) -> bytes:
        header = bytearray(self.HEADER_SIZE)
        header[0:4] = self.MAGIC
        header[4:8] = struct.pack("<I", self.VERSION)
        header[8:12] = struct.pack("<I", self.block_size)
        header[12:20] = struct.pack("<Q", self.total_blocks)
        return bytes(header)

    def _load_index(self) -> None:
        index_path = self.path / "index.json"
        if index_path.exists():
            with open(index_path, "r") as f:
                data = json.load(f)
                self._free_blocks = set(data.get("free_blocks", []))
                self._used_blocks = set(data.get("used_blocks", []))

    def _save_index(self) -> None:
        index_path = self.path / "index.json"
        with open(index_path, "w") as f:
            json.dump({
                "free_blocks": sorted(self._free_blocks),
                "used_blocks": sorted(self._used_blocks),
                "total_blocks": self.total_blocks,
                "block_size": self.block_size,
            }, f)

    def _block_offset(self, block_id: int) -> int:
        return self.HEADER_SIZE + block_id * self.block_size

    def read(self, block_id: int) -> bytes:
        if not self._data_file:
            raise RuntimeError("Backend not initialized")

        offset = self._block_offset(block_id)
        self._data_file.seek(offset)
        return self._data_file.read(self.block_size)

    def write(self, block_id: int, data: bytes, offset: int = 0) -> int:
        if not self._data_file:
            raise RuntimeError("Backend not initialized")

        block_offset = self._block_offset(block_id) + offset
        self._data_file.seek(block_offset)
        write_len = min(len(data), self.block_size - offset)
        self._data_file.write(data[:write_len])
        return write_len

    def allocate_blocks(self, count: int) -> List[int]:
        if len(self._free_blocks) < count:
            raise RuntimeError(f"Cannot allocate {count} blocks")

        allocated = []
        for _ in range(count):
            block_id = min(self._free_blocks)
            self._free_blocks.remove(block_id)
            self._used_blocks.add(block_id)
            allocated.append(block_id)

        self._save_index()
        return allocated

    def free_blocks(self, block_ids: List[int]) -> None:
        for block_id in block_ids:
            if block_id in self._used_blocks:
                self._used_blocks.remove(block_id)
                self._free_blocks.add(block_id)

                offset = self._block_offset(block_id)
                self._data_file.seek(offset)
                self._data_file.write(b"\x00" * self.block_size)

        self._save_index()

    def sync(self) -> None:
        if self._data_file:
            self._data_file.flush()
            os.fsync(self._data_file.fileno())
        self._sync_count += 1

    def close(self) -> None:
        if self._data_file:
            self.sync()
            self._data_file.close()
            self._data_file = None
        self._save_index()
        self._initialized = False

    def get_info(self) -> dict:
        return {
            "type": "disk",
            "path": str(self.path),
            "block_size": self.block_size,
            "total_blocks": self.total_blocks,
            "free_blocks": len(self._free_blocks),
            "used_blocks": len(self._used_blocks),
            "sync_count": self._sync_count,
            "initialized": self._initialized,
        }

    def used_blocks(self) -> List[int]:
        return sorted(self._used_blocks)

    def free_block_count(self) -> int:
        return len(self._free_blocks)

    def used_block_count(self) -> int:
        return len(self._used_blocks)
