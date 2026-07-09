"""Storage backend interface for ArcanisFileSystem.

Defines the abstract interface for storage implementations.
"""

import abc
from typing import BinaryIO, Optional


class StorageBackend(abc.ABC):
    """Abstract base class for storage backends."""

    @abc.abstractmethod
    def read(self, block_id: int) -> bytes:
        """Read data from a block."""
        pass

    @abc.abstractmethod
    def write(self, block_id: int, data: bytes, offset: int = 0) -> int:
        """Write data to a block."""
        pass

    @abc.abstractmethod
    def allocate_blocks(self, count: int) -> list:
        """Allocate contiguous blocks."""
        pass

    @abc.abstractmethod
    def free_blocks(self, block_ids: list) -> None:
        """Free allocated blocks."""
        pass

    @abc.abstractmethod
    def sync(self) -> None:
        """Flush all pending writes to storage."""
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Close the storage backend."""
        pass

    @abc.abstractmethod
    def get_info(self) -> dict:
        """Get storage backend information."""
        pass
