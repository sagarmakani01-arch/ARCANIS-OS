"""Tests for storage backends."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from storage.memory import MemoryBackend
from storage.disk import DiskBackend


class TestMemoryBackend(unittest.TestCase):
    def test_write_read(self):
        backend = MemoryBackend(block_size=1024, total_blocks=100)
        blocks = backend.allocate_blocks(1)
        data = b"Hello, World!"
        backend.write(blocks[0], data)
        read_data = backend.read(blocks[0])
        self.assertEqual(read_data[:len(data)], data)

    def test_allocate_free(self):
        backend = MemoryBackend(block_size=1024, total_blocks=100)
        blocks = backend.allocate_blocks(10)
        self.assertEqual(len(blocks), 10)
        self.assertEqual(backend.used_block_count(), 10)
        backend.free_blocks(blocks)
        self.assertEqual(backend.free_block_count(), 100)

    def test_info(self):
        backend = MemoryBackend()
        info = backend.get_info()
        self.assertIn("type", info)
        self.assertEqual(info["type"], "memory")

    def test_multiple_writes(self):
        backend = MemoryBackend(block_size=1024, total_blocks=100)
        blocks = backend.allocate_blocks(3)
        for i, block_id in enumerate(blocks):
            data = f"Block {i}".encode()
            backend.write(block_id, data)
        for i, block_id in enumerate(blocks):
            data = backend.read(block_id)
            self.assertIn(f"Block {i}".encode(), data)


class TestDiskBackend(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_read(self):
        backend = DiskBackend(self.test_dir, block_size=1024, total_blocks=100)
        blocks = backend.allocate_blocks(1)
        data = b"Hello, Disk!"
        backend.write(blocks[0], data)
        read_data = backend.read(blocks[0])
        self.assertEqual(read_data[:len(data)], data)
        backend.close()

    def test_allocate_free(self):
        backend = DiskBackend(self.test_dir, block_size=1024, total_blocks=100)
        blocks = backend.allocate_blocks(5)
        self.assertEqual(len(blocks), 5)
        backend.free_blocks(blocks)
        self.assertEqual(backend.free_block_count(), 100)
        backend.close()

    def test_info(self):
        backend = DiskBackend(self.test_dir, block_size=1024, total_blocks=100)
        info = backend.get_info()
        self.assertIn("type", info)
        self.assertEqual(info["type"], "disk")
        backend.close()

    def test_sync(self):
        backend = DiskBackend(self.test_dir, block_size=1024, total_blocks=100)
        blocks = backend.allocate_blocks(1)
        backend.write(blocks[0], b"sync test")
        backend.sync()
        info = backend.get_info()
        self.assertGreater(info["sync_count"], 0)
        backend.close()


if __name__ == "__main__":
    unittest.main()
