"""Block allocation system for ArcanisFileSystem.

Manages the allocation and deallocation of storage blocks.
Supports direct, indirect, and double-indirect block pointers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class Block:
    """Represents a single storage block."""

    id: int
    data: bytes = b""
    size: int = 4096

    def __post_init__(self):
        if len(self.data) > self.size:
            raise ValueError(f"Block data ({len(self.data)} bytes) exceeds block size ({self.size} bytes)")
        if len(self.data) < self.size:
            self.data = self.data + b"\x00" * (self.size - len(self.data))

    def is_free(self) -> bool:
        return self.data == b"\x00" * self.size

    def write(self, data: bytes, offset: int = 0) -> int:
        if offset < 0 or offset >= self.size:
            raise ValueError(f"Offset {offset} out of range (0-{self.size - 1})")

        available = self.size - offset
        write_len = min(len(data), available)
        self.data = self.data[:offset] + data[:write_len] + self.data[offset + write_len:]
        return write_len

    def read(self, offset: int = 0, length: int = -1) -> bytes:
        if offset < 0 or offset >= self.size:
            raise ValueError(f"Offset {offset} out of range (0-{self.size - 1})")

        if length < 0:
            return self.data[offset:]
        return self.data[offset:offset + length]

    def clear(self) -> None:
        self.data = b"\x00" * self.size


class BlockAllocator:
    """Manages block allocation with free-space bitmap."""

    DIRECT_BLOCKS = 12
    SINGLE_INDIRECT_PTRS = 1024
    DOUBLE_INDIRECT_PTRS = 1024

    def __init__(self, total_blocks: int = 1048576, block_size: int = 4096):
        self.total_blocks = total_blocks
        self.block_size = block_size
        self._blocks: dict = {}
        self._free_blocks: Set[int] = set(range(total_blocks))
        self._used_blocks: Set[int] = set()
        self._initialize_blocks()

    def _initialize_blocks(self) -> None:
        for i in range(min(self.total_blocks, 10000)):
            self._blocks[i] = Block(id=i, size=self.block_size)

    def allocate(self, count: int = 1) -> List[int]:
        if len(self._free_blocks) < count:
            raise RuntimeError(f"Cannot allocate {count} blocks: only {len(self._free_blocks)} free")

        allocated = []
        for _ in range(count):
            block_id = min(self._free_blocks)
            self._free_blocks.remove(block_id)
            self._used_blocks.add(block_id)
            allocated.append(block_id)

            if block_id not in self._blocks:
                self._blocks[block_id] = Block(id=block_id, size=self.block_size)

        return allocated

    def free(self, block_ids: List[int]) -> None:
        for block_id in block_ids:
            if block_id in self._used_blocks:
                self._used_blocks.remove(block_id)
                self._free_blocks.add(block_id)
                if block_id in self._blocks:
                    self._blocks[block_id].clear()

    def read_block(self, block_id: int) -> Block:
        if block_id not in self._blocks:
            raise KeyError(f"Block {block_id} does not exist")
        return self._blocks[block_id]

    def write_block(self, block_id: int, data: bytes, offset: int = 0) -> int:
        if block_id not in self._blocks:
            raise KeyError(f"Block {block_id} does not exist")
        return self._blocks[block_id].write(data, offset)

    def is_allocated(self, block_id: int) -> bool:
        return block_id in self._used_blocks

    def free_count(self) -> int:
        return len(self._free_blocks)

    def used_count(self) -> int:
        return len(self._used_blocks)

    def usage_percent(self) -> float:
        if self.total_blocks == 0:
            return 0.0
        return (self.used_count() / self.total_blocks) * 100

    def max_file_size(self) -> int:
        single = self.DIRECT_BLOCKS * self.block_size
        indirect = self.SINGLE_INDIRECT_PTRS * self.block_size
        double_indirect = self.DOUBLE_INDIRECT_PTRS * self.SINGLE_INDIRECT_PTRS * self.block_size
        return single + indirect + double_indirect

    def clear(self) -> None:
        for block in self._blocks.values():
            block.clear()
        self._free_blocks = set(range(self.total_blocks))
        self._used_blocks.clear()
