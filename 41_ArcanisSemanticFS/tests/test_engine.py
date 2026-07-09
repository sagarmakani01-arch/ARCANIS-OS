import tempfile
from pathlib import Path

import pytest

from arcanis_semantic_fs.engine import SemanticFSEngine
from arcanis_semantic_fs.config import SemanticFSConfig
from arcanis_semantic_fs.storage import MetadataStore, FileEntity, Relationship
from arcanis_semantic_fs.indexer import ContentAnalyzer, EmbeddingIndex


class TestMetadataStore:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = Path(self.tmp) / "test.db"
        self.store = MetadataStore(self.db_path)

    def teardown_method(self):
        self.store.close()

    def test_upsert_and_get(self):
        entity = FileEntity(path="/test.py", name="test.py", content_type="python", size=100)
        self.store.upsert_file(entity)
        retrieved = self.store.get_file(entity.id)
        assert retrieved is not None
        assert retrieved.name == "test.py"
        assert retrieved.content_type == "python"

    def test_get_by_path(self):
        entity = FileEntity(path="/src/main.py", name="main.py")
        self.store.upsert_file(entity)
        found = self.store.get_file_by_path("/src/main.py")
        assert found is not None

    def test_search(self):
        self.store.upsert_file(FileEntity(path="/a.py", name="auth.py", summary="authentication"))
        self.store.upsert_file(FileEntity(path="/b.py", name="utils.py", summary="utilities"))
        results = self.store.search_files("auth")
        assert len(results) >= 1
        assert any("auth" in r.name.lower() or "auth" in (r.summary or "").lower() for r in results)

    def test_delete(self):
        entity = FileEntity(path="/del.py", name="del.py")
        self.store.upsert_file(entity)
        assert self.store.delete_file(entity.id)
        assert self.store.get_file(entity.id) is None

    def test_relationships(self):
        a = FileEntity(path="/a.py", name="a.py")
        b = FileEntity(path="/b.py", name="b.py")
        self.store.upsert_file(a)
        self.store.upsert_file(b)
        self.store.add_relationship(Relationship(source_id=a.id, target_id=b.id, rel_type="depends_on"))
        related = self.store.get_related(a.id)
        assert len(related) == 1
        assert related[0].id == b.id

    def test_stats(self):
        self.store.upsert_file(FileEntity(path="/x.py", name="x.py"))
        stats = self.store.get_stats()
        assert stats["files"] == 1


class TestContentAnalyzer:
    def setup_method(self):
        self.analyzer = ContentAnalyzer()

    def test_extract_tags_python(self):
        content = "class Foo:\n    def bar(self):\n        pass"
        tags = self.analyzer.extract_tags(content, "python")
        assert any("defines:Foo" in t for t in tags)
        assert any("defines:bar" in t for t in tags)

    def test_generate_summary_code(self):
        content = "class Engine:\n    def run(self): pass\ndef main(): pass"
        summary = self.analyzer.generate_summary(content, "app.py", "python")
        assert "app.py" in summary
        assert "Engine" in summary or "main" in summary

    def test_detect_intent(self):
        assert self.analyzer.detect_intent("", "test_app.py") == "testing"
        assert self.analyzer.detect_intent("", "config.yaml") == "configuration"
        assert self.analyzer.detect_intent("", "README.md") == "documentation"
        assert self.analyzer.detect_intent("", "main.py") == "entry_point"

    def test_extract_imports(self):
        content = "import os\nfrom pathlib import Path\nimport json"
        imports = self.analyzer.extract_imports(content, "python")
        assert "os" in imports


class TestEmbeddingIndex:
    def test_add_and_search(self):
        idx = EmbeddingIndex(dim=3)
        idx.add("a", [1.0, 0.0, 0.0])
        idx.add("b", [0.0, 1.0, 0.0])
        idx.add("c", [0.9, 0.1, 0.0])
        results = idx.search([1.0, 0.0, 0.0], top_k=2)
        assert results[0][0] == "a"
        assert results[1][0] == "c"

    def test_remove(self):
        idx = EmbeddingIndex(dim=2)
        idx.add("x", [1.0, 0.0])
        idx.remove("x")
        assert "x" not in idx._vectors


class TestSemanticFSEngine:
    def setup_method(self):
        self.tmp = Path(tempfile.mkdtemp())
        config = SemanticFSConfig(root_path=self.tmp, db_path=self.tmp / "test.db")
        self.engine = SemanticFSEngine(config)

    def teardown_method(self):
        self.engine.close()

    def test_index_file(self):
        test_file = self.tmp / "hello.py"
        test_file.write_text("def hello():\n    print('hi')\n")
        entity = self.engine.index_file(test_file)
        assert entity is not None
        assert entity.name == "hello.py"
        assert entity.content_type == "python"

    def test_search_keyword(self):
        f = self.tmp / "auth.py"
        f.write_text("class Auth: pass")
        self.engine.index_file(f)
        results = self.engine.search("auth")
        assert len(results) >= 1

    def test_suggest_organization(self):
        (self.tmp / "main.py").write_text("x = 1")
        (self.tmp / "test_main.py").write_text("x = 2")
        (self.tmp / "README.md").write_text("# Hello")
        suggestion = self.engine.suggest_organization()
        assert suggestion.current_files == 3
        assert suggestion.confidence > 0

    def test_stats(self):
        stats = self.engine.get_stats()
        assert "files_indexed" in stats
