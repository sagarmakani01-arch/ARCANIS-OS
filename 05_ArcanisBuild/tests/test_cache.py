"""Tests for build cache."""

import os
import tempfile
import unittest
import json

from arcanis_build.cache import BuildCache, CacheEntry


class TestBuildCache(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, ".arcanis-cache")
        self.cache = BuildCache(self.cache_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_put_and_get(self):
        artifact = os.path.join(self.temp_dir, "output.bin")
        with open(artifact, "w") as f:
            f.write("built artifact")

        inputs = {"src/main.arc": "abc123", "src/lib.arc": "def456"}
        self.cache.put("my-target", inputs, artifact)

        cached = self.cache.get("my-target", inputs)
        self.assertIsNotNone(cached)
        self.assertTrue(os.path.exists(cached))

    def test_cache_miss(self):
        inputs = {"src/main.arc": "wronghash"}
        cached = self.cache.get("my-target", inputs)
        self.assertIsNone(cached)

    def test_cache_clear(self):
        artifact = os.path.join(self.temp_dir, "output.bin")
        with open(artifact, "w") as f:
            f.write("data")

        self.cache.put("t1", {"a": "1"}, artifact)
        self.cache.put("t2", {"b": "2"}, artifact)
        self.assertEqual(len(self.cache._entries), 2)

        self.cache.clear()
        self.assertEqual(len(self.cache._entries), 0)

    def test_cache_persistence(self):
        artifact = os.path.join(self.temp_dir, "output.bin")
        with open(artifact, "w") as f:
            f.write("data")

        inputs = {"f1": "hash1"}
        self.cache.put("target", inputs, artifact)

        cache2 = BuildCache(self.cache_dir)
        cached = cache2.get("target", inputs)
        self.assertIsNotNone(cached)

    def test_cache_prune(self):
        artifact = os.path.join(self.temp_dir, "output.bin")
        with open(artifact, "w") as f:
            f.write("data")

        for i in range(10):
            self.cache.put(f"target-{i}", {f"f{i}": str(i)}, artifact)

        self.assertEqual(len(self.cache._entries), 10)
        self.cache.prune(max_entries=5)
        self.assertLessEqual(len(self.cache._entries), 5)

    def test_cache_stats(self):
        artifact = os.path.join(self.temp_dir, "output.bin")
        with open(artifact, "w") as f:
            f.write("data")

        self.cache.put("t", {"a": "1"}, artifact)
        stats = self.cache.stats()
        self.assertEqual(stats["entries"], 1)
        self.assertEqual(stats["cache_dir"], self.cache_dir)
        self.assertGreater(stats["size_bytes"], 0)


class TestCacheEntry(unittest.TestCase):
    def test_entry_roundtrip(self):
        entry = CacheEntry("key123", "/path/to/artifact", {"version": "1"})
        data = entry.to_dict()
        restored = CacheEntry.from_dict(data)
        self.assertEqual(restored.key, "key123")
        self.assertEqual(restored.artifact_path, "/path/to/artifact")
        self.assertEqual(restored.metadata["version"], "1")


if __name__ == "__main__":
    unittest.main()
