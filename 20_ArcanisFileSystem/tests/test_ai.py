"""Tests for AI features."""

import os
import sys
import uuid
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai.embeddings import EmbeddingEngine, FileEmbedding
from ai.indexer import AutoIndexer, IndexType
from ai.search import SemanticSearch, SearchQuery, SearchMode
from ai.organizer import SmartOrganizer, OrganizationRule, OrganizeAction, MatchCondition


class TestEmbeddingEngine(unittest.TestCase):
    def test_generate_embedding(self):
        engine = EmbeddingEngine()
        inode_id = uuid.uuid4()
        embedding = engine.generate_embedding(inode_id, b"Hello world test content")
        self.assertIsNotNone(embedding)
        self.assertEqual(len(embedding.vector), 128)

    def test_similarity(self):
        engine = EmbeddingEngine()
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        engine.generate_embedding(id1, b"similar content here")
        engine.generate_embedding(id2, b"similar content here")
        emb1 = engine.get_embedding(id1)
        emb2 = engine.get_embedding(id2)
        self.assertIsNotNone(emb1)
        self.assertIsNotNone(emb2)
        self.assertEqual(len(emb1.vector), len(emb2.vector))

    def test_find_similar(self):
        engine = EmbeddingEngine()
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        engine.generate_embedding(id1, b"document about cats")
        engine.generate_embedding(id2, b"document about dogs")
        embedding = engine.get_embedding(id1)
        similar = engine.find_similar(embedding.vector, top_k=5)
        self.assertGreater(len(similar), 0)

    def test_remove_embedding(self):
        engine = EmbeddingEngine()
        inode_id = uuid.uuid4()
        engine.generate_embedding(inode_id, b"test content")
        self.assertTrue(engine.remove_embedding(inode_id))
        self.assertIsNone(engine.get_embedding(inode_id))


class TestAutoIndexer(unittest.TestCase):
    def test_index_file(self):
        indexer = AutoIndexer()
        inode_id = uuid.uuid4()
        entry = indexer.index_file(inode_id, "/test.txt", b"Hello world")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.path, "/test.txt")

    def test_search_keywords(self):
        indexer = AutoIndexer()
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        indexer.index_file(id1, "/doc1.txt", b"python programming tutorial")
        indexer.index_file(id2, "/doc2.txt", b"java programming guide")
        results = indexer.search_keywords(["python"])
        self.assertEqual(len(results), 1)

    def test_search_by_tag(self):
        indexer = AutoIndexer()
        inode_id = uuid.uuid4()
        indexer.index_file(inode_id, "/image.jpg", metadata={"tags": "photo, nature"})
        results = indexer.search_by_tag("photo")
        self.assertEqual(len(results), 1)

    def test_remove_index(self):
        indexer = AutoIndexer()
        inode_id = uuid.uuid4()
        indexer.index_file(inode_id, "/test.txt", b"content")
        self.assertTrue(indexer.remove_index(inode_id))

    def test_statistics(self):
        indexer = AutoIndexer()
        indexer.index_file(uuid.uuid4(), "/a.txt", b"content a")
        indexer.index_file(uuid.uuid4(), "/b.txt", b"content b")
        stats = indexer.get_statistics()
        self.assertEqual(stats["total_entries"], 2)


class TestSemanticSearch(unittest.TestCase):
    def test_keyword_search(self):
        indexer = AutoIndexer()
        indexer.index_file(uuid.uuid4(), "/test.py", b"python code example")
        search = SemanticSearch(indexer=indexer)
        query = SearchQuery(text="python", mode=SearchMode.KEYWORD)
        results = search.search(query)
        self.assertGreater(len(results), 0)

    def test_quick_search(self):
        indexer = AutoIndexer()
        indexer.index_file(uuid.uuid4(), "/readme.md", b"documentation file")
        search = SemanticSearch(indexer=indexer)
        results = search.quick_search("documentation")
        self.assertGreater(len(results), 0)

    def test_suggest(self):
        search = SemanticSearch()
        search._query_suggestions = {"python tutorial": 5, "python basics": 3}
        suggestions = search.suggest("pyt")
        self.assertGreater(len(suggestions), 0)


class TestSmartOrganizer(unittest.TestCase):
    def test_create_rule(self):
        organizer = SmartOrganizer()
        rule = OrganizationRule(
            name="Test Rule",
            conditions=[(MatchCondition.EXTENSION, "txt")],
            action=OrganizeAction.MOVE,
            target_path="/Documents/{name}{ext}",
        )
        organizer.add_rule(rule)
        self.assertEqual(len(organizer.list_rules()), 1)

    def test_match_rule(self):
        organizer = SmartOrganizer()
        rule = OrganizationRule(
            name="Image Rule",
            conditions=[(MatchCondition.EXTENSION, "jpg")],
            action=OrganizeAction.MOVE,
            target_path="/Images/{name}{ext}",
        )
        organizer.add_rule(rule)
        file_info = {"name": "photo.jpg", "extension": "jpg", "path": "/photo.jpg"}
        matching = organizer.find_matching_rules(file_info)
        self.assertEqual(len(matching), 1)

    def test_default_rules(self):
        organizer = SmartOrganizer()
        organizer.create_default_rules()
        rules = organizer.list_rules()
        self.assertGreater(len(rules), 0)

    def test_statistics(self):
        organizer = SmartOrganizer()
        organizer.create_default_rules()
        stats = organizer.get_statistics()
        self.assertIn("total_rules", stats)


if __name__ == "__main__":
    unittest.main()
