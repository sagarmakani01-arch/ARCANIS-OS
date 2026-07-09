"""Tests for core filesystem components."""

import os
import sys
import time
import uuid
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.inode import Inode, InodeType, InodeTable
from core.blocks import Block, BlockAllocator
from core.directory import Directory, DirectoryTree, EntryType, DirectoryEntry
from core.metadata import MetadataManager, MetadataType, FileMetadata
from core.filesystem import ArcanisFileSystem


class TestInode(unittest.TestCase):
    def test_inode_creation(self):
        inode = Inode()
        self.assertEqual(inode.inode_type, InodeType.FILE)
        self.assertEqual(inode.size, 0)
        self.assertEqual(inode.permissions, 0o644)
        self.assertEqual(inode.reference_count, 1)

    def test_inode_type(self):
        for itype in InodeType:
            inode = Inode(inode_type=itype)
            self.assertEqual(inode.inode_type, itype)

    def test_inode_touch(self):
        inode = Inode()
        old_access = inode.accessed_at
        time.sleep(0.01)
        inode.touch_access()
        self.assertGreater(inode.accessed_at, old_access)

    def test_inode_permissions(self):
        inode = Inode()
        inode.update_permissions(0o755)
        self.assertEqual(inode.permissions, 0o755)

    def test_inode_extended_attrs(self):
        inode = Inode()
        inode.set_extended_attr("author", "test")
        self.assertEqual(inode.get_extended_attr("author"), "test")
        self.assertTrue(inode.remove_extended_attr("author"))
        self.assertIsNone(inode.get_extended_attr("author"))

    def test_inode_blocks_needed(self):
        inode = Inode(size=8192)
        self.assertEqual(inode.calculate_blocks_needed(4096), 2)
        inode.size = 4097
        self.assertEqual(inode.calculate_blocks_needed(4096), 2)
        inode.size = 8193
        self.assertEqual(inode.calculate_blocks_needed(4096), 3)

    def test_inode_to_dict(self):
        inode = Inode()
        d = inode.to_dict()
        self.assertIn("id", d)
        self.assertIn("type", d)
        self.assertIn("size", d)


class TestInodeTable(unittest.TestCase):
    def test_allocate(self):
        table = InodeTable()
        inode = table.allocate()
        self.assertIsNotNone(inode)
        self.assertEqual(table.count(), 1)

    def test_get(self):
        table = InodeTable()
        inode = table.allocate()
        retrieved = table.get(inode.id)
        self.assertEqual(inode.id, retrieved.id)

    def test_remove(self):
        table = InodeTable()
        inode = table.allocate()
        self.assertTrue(table.remove(inode.id))
        self.assertEqual(table.count(), 0)

    def test_find_by_type(self):
        table = InodeTable()
        table.allocate(InodeType.FILE)
        table.allocate(InodeType.DIRECTORY)
        files = table.find_by_type(InodeType.FILE)
        self.assertEqual(len(files), 1)


class TestBlock(unittest.TestCase):
    def test_block_creation(self):
        block = Block(id=0, size=1024)
        self.assertEqual(block.size, 1024)
        self.assertTrue(block.is_free())

    def test_block_write_read(self):
        block = Block(id=0, size=1024)
        data = b"Hello, Arcanis!"
        written = block.write(data)
        self.assertEqual(written, len(data))
        read_data = block.read(0, len(data))
        self.assertEqual(read_data, data)

    def test_block_clear(self):
        block = Block(id=0, size=1024)
        block.write(b"test")
        block.clear()
        self.assertTrue(block.is_free())


class TestBlockAllocator(unittest.TestCase):
    def test_allocate(self):
        allocator = BlockAllocator(total_blocks=100)
        blocks = allocator.allocate(5)
        self.assertEqual(len(blocks), 5)
        self.assertEqual(allocator.used_count(), 5)

    def test_free(self):
        allocator = BlockAllocator(total_blocks=100)
        blocks = allocator.allocate(5)
        allocator.free(blocks)
        self.assertEqual(allocator.free_count(), 100)

    def test_max_file_size(self):
        allocator = BlockAllocator()
        max_size = allocator.max_file_size()
        self.assertGreater(max_size, 0)


class TestDirectory(unittest.TestCase):
    def test_add_entry(self):
        dir_inode = uuid.uuid4()
        directory = Directory(inode_id=dir_inode)
        entry = directory.add_entry("test.txt", uuid.uuid4())
        self.assertEqual(entry.name, "test.txt")

    def test_remove_entry(self):
        dir_inode = uuid.uuid4()
        directory = Directory(inode_id=dir_inode)
        file_id = uuid.uuid4()
        directory.add_entry("test.txt", file_id)
        removed = directory.remove_entry("test.txt")
        self.assertIsNotNone(removed)

    def test_rename_entry(self):
        dir_inode = uuid.uuid4()
        directory = Directory(inode_id=dir_inode)
        file_id = uuid.uuid4()
        directory.add_entry("old.txt", file_id)
        result = directory.rename_entry("old.txt", "new.txt")
        self.assertTrue(result)
        self.assertIsNotNone(directory.get_entry("new.txt"))

    def test_list_entries(self):
        dir_inode = uuid.uuid4()
        directory = Directory(inode_id=dir_inode)
        directory.add_entry("b.txt", uuid.uuid4())
        directory.add_entry("a.txt", uuid.uuid4())
        entries = directory.list_entries()
        self.assertEqual(entries[0].name, "a.txt")

    def test_invalid_name(self):
        dir_inode = uuid.uuid4()
        directory = Directory(inode_id=dir_inode)
        with self.assertRaises(ValueError):
            directory.add_entry("/", uuid.uuid4())
        with self.assertRaises(ValueError):
            directory.add_entry(".", uuid.uuid4())


class TestDirectoryTree(unittest.TestCase):
    def test_create_directory(self):
        tree = DirectoryTree()
        dir_inode = uuid.uuid4()
        directory = tree.create_directory(dir_inode)
        self.assertIsNotNone(directory)

    def test_get_directory(self):
        tree = DirectoryTree()
        dir_inode = uuid.uuid4()
        tree.create_directory(dir_inode)
        retrieved = tree.get_directory(dir_inode)
        self.assertIsNotNone(retrieved)

    def test_parent_child(self):
        tree = DirectoryTree()
        parent_id = uuid.uuid4()
        child_id = uuid.uuid4()
        tree.create_directory(parent_id)
        tree.create_directory(child_id, parent_id)

        parent = tree.get_parent(child_id)
        self.assertIsNotNone(parent)
        self.assertEqual(parent.inode_id, parent_id)


class TestMetadataManager(unittest.TestCase):
    def test_create(self):
        manager = MetadataManager()
        inode_id = uuid.uuid4()
        metadata = manager.create(inode_id)
        self.assertIsNotNone(metadata)
        self.assertTrue(manager.exists(inode_id))

    def test_set_get(self):
        manager = MetadataManager()
        inode_id = uuid.uuid4()
        manager.create(inode_id)
        manager.set_field(inode_id, "author", "test")
        value = manager.get_field(inode_id, "author")
        self.assertEqual(value, "test")

    def test_search(self):
        manager = MetadataManager()
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        manager.create(id1)
        manager.create(id2)
        manager.set_field(id1, "type", "image")
        manager.set_field(id2, "type", "document")
        results = manager.search_by_field("type", "image")
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
