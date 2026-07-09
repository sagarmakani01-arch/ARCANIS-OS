"""Integration tests for ArcanisFileSystem."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.filesystem import ArcanisFileSystem
from storage.memory import MemoryBackend


class TestArcanisFileSystem(unittest.TestCase):
    def setUp(self):
        self.fs = ArcanisFileSystem(enable_ai=False)

    def tearDown(self):
        self.fs.unmount()

    def test_filesystem_info(self):
        info = self.fs.get_info()
        self.assertIn("version", info)
        self.assertTrue(info["mounted"])

    def test_create_file(self):
        inode_id = self.fs.create_file("/test.txt", b"Hello, World!")
        self.assertIsNotNone(inode_id)
        content = self.fs.read_file("/test.txt")
        self.assertEqual(content, b"Hello, World!")

    def test_create_directory(self):
        inode_id = self.fs.create_directory("/documents")
        self.assertIsNotNone(inode_id)
        entries = self.fs.list_directory("/")
        names = [e.name for e in entries]
        self.assertIn("documents", names)

    def test_write_read_file(self):
        self.fs.create_file("/test.txt", b"initial")
        self.fs.write_file("/test.txt", b"updated")
        content = self.fs.read_file("/test.txt")
        self.assertEqual(content, b"updated")

    def test_append_file(self):
        self.fs.create_file("/test.txt", b"Hello")
        self.fs.write_file("/test.txt", b" World", append=True)
        content = self.fs.read_file("/test.txt")
        self.assertEqual(content, b"Hello World")

    def test_delete_file(self):
        self.fs.create_file("/test.txt", b"delete me")
        result = self.fs.delete_file("/test.txt")
        self.assertTrue(result)

    def test_rename_file(self):
        self.fs.create_file("/old.txt", b"content")
        self.fs.rename("/old.txt", "/new.txt")
        content = self.fs.read_file("/new.txt")
        self.assertEqual(content, b"content")

    def test_chmod(self):
        inode_id = self.fs.create_file("/test.txt", b"content", permissions=0o644)
        self.fs.chmod("/test.txt", 0o755)
        stat = self.fs.stat("/test.txt")
        self.assertEqual(stat["permissions"], oct(0o755))

    def test_stat(self):
        self.fs.create_file("/test.txt", b"content")
        stat = self.fs.stat("/test.txt")
        self.assertIn("type", stat)
        self.assertEqual(stat["type"], "FILE")

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.fs.read_file("/nonexistent.txt")

    def test_directory_listing(self):
        self.fs.create_file("/a.txt", b"a")
        self.fs.create_file("/b.txt", b"b")
        self.fs.create_directory("/subdir")
        entries = self.fs.list_directory("/")
        self.assertGreaterEqual(len(entries), 3)

    def test_nested_directories(self):
        self.fs.create_directory("/a")
        self.fs.create_directory("/a/b")
        self.fs.create_directory("/a/b/c")
        self.fs.create_file("/a/b/c/file.txt", b"nested")
        content = self.fs.read_file("/a/b/c/file.txt")
        self.assertEqual(content, b"nested")

    def test_delete_directory(self):
        self.fs.create_directory("/empty_dir")
        result = self.fs.delete_directory("/empty_dir")
        self.assertTrue(result)

    def test_delete_nonempty_directory(self):
        self.fs.create_directory("/dir")
        self.fs.create_file("/dir/file.txt", b"content")
        with self.assertRaises(OSError):
            self.fs.delete_directory("/dir")

    def test_snapshot(self):
        self.fs.create_file("/test.txt", b"content")
        snap = self.fs.snapshot("test_backup")
        self.assertIsNotNone(snap)

    def test_context_manager(self):
        with ArcanisFileSystem() as fs:
            fs.create_file("/test.txt", b"content")
            content = fs.read_file("/test.txt")
            self.assertEqual(content, b"content")


class TestArcanisFileSystemAI(unittest.TestCase):
    def setUp(self):
        self.fs = ArcanisFileSystem(enable_ai=True)

    def tearDown(self):
        self.fs.unmount()

    def test_index_all(self):
        self.fs.create_file("/test1.txt", b"python programming")
        self.fs.create_file("/test2.txt", b"java programming")
        count = self.fs.index_all()
        self.assertEqual(count, 2)

    def test_search(self):
        self.fs.create_file("/doc.txt", b"documentation about testing")
        self.fs.index_all()
        results = self.fs.search("testing")
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
