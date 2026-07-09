"""In-memory storage backend for ArcanisFileSystem.

Used for testing and ephemeral filesystems.
"""

from typing import Dict, List, Set
from .backend import StorageBackend


class MemoryBackend(StorageBackend):
    """In-memory block storage backend."""

    def __init__(self, block_size: int = 4096, total_blocks: int = 100000):
        self.block_size = block_size
        self.total_blocks = total_blocks
        self._blocks: Dict[int, bytearray] = {}
        self._free_blocks: Set[int] = set(range(total_blocks))
        self._used_blocks: Set[int] = set()
        self._sync_count = 0

    def read(self, block_id: int) -> bytes:
        if block_id not in self._blocks:
            return b"\x00" * self.block_size
        return bytes(self._blocks[block_id])

    def write(self, block_id: int, data: bytes, offset: int = 0) -> int:
        if block_id not in self._blocks:
            self._blocks[block_id] = bytearray(b"\x00" * self.block_size)

        block = self._blocks[block_id]
        available = self.block_size - offset
        write_len = min(len(data), available)

        block[offset:offset + write_len] = data[:write_len]
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
            self._blocks[block_id] = bytearray(b"\x00" * self.block_size)

        return allocated

    def free_blocks(self, block_ids: List[int]) -> None:
        for block_id in block_ids:
            if block_id in self._used_blocks:
                self._used_blocks.remove(block_id)
                self._free_blocks.add(block_id)
                self._blocks.pop(block_id, None)

    def sync(self) -> None:
        self._sync_count += 1

    def close(self) -> None:
        self._blocks.clear()
        self._free_blocks.clear()
        self._used_blocks.clear()

    def get_info(self) -> dict:
        return {
            "type": "memory",
            "block_size": self.block_size,
            "total_blocks": self.total_blocks,
            "free_blocks": len(self._free_blocks),
            "used_blocks": len(self._used_blocks),
            "sync_count": self._sync_count,
        }

    def used_blocks(self) -> List[int]:
        return sorted(self._used_blocks)

    def free_block_count(self) -> int:
        return len(self._free_blocks)

    def used_block_count(self) -> int:
        return len(self._used_blocks)
