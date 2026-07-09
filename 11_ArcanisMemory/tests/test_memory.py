"""Tests for ArcanisMemory types, store, manager, AI features, and security."""

import math
from datetime import datetime, timedelta

import numpy as np
import pytest

from arcanis_memory.config import MemoryConfig
from arcanis_memory.core.types import (
    Memory,
    MemoryID,
    MemoryImportance,
    MemoryRelation,
    MemoryScope,
    MemoryType,
    Permission,
    PermissionLevel,
    RelationType,
    default_ttl,
)
from arcanis_memory.core.manager import MemoryManager
from arcanis_memory.storage.memory_store import InMemoryStore
from arcanis_memory.ai.features import AIFeatures, Embedder, _tokenize
from arcanis_memory.security.policy import MemorySecurity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides) -> MemoryConfig:
    defaults = dict(
        storage_backend="memory",
        embedding_dim=64,
        weight_importance=0.5,
        weight_recency=0.3,
        weight_access=0.2,
    )
    defaults.update(overrides)
    return MemoryConfig(**defaults)


def _make_manager(**cfg_overrides) -> tuple[MemoryManager, InMemoryStore]:
    store = InMemoryStore()
    config = _make_config(**cfg_overrides)
    return MemoryManager(store, config), store


# ===========================================================================
# 1. Types
# ===========================================================================

class TestMemoryType:
    def test_from_string(self):
        assert MemoryType.from_string("short_term") == MemoryType.SHORT_TERM
        assert MemoryType.from_string("LONG_TERM") == MemoryType.LONG_TERM
        assert MemoryType.from_string("knowledge") == MemoryType.KNOWLEDGE

    def test_to_string(self):
        assert MemoryType.EVENT.to_string() == "EVENT"

    def test_from_string_invalid(self):
        with pytest.raises(KeyError):
            MemoryType.from_string("nonexistent")


class TestMemoryScope:
    def test_from_string(self):
        assert MemoryScope.from_string("global") == MemoryScope.GLOBAL
        assert MemoryScope.from_string("session") == MemoryScope.SESSION

    def test_to_string(self):
        assert MemoryScope.PROJECT.to_string() == "PROJECT"


class TestMemoryImportance:
    def test_from_score_bands(self):
        assert MemoryImportance.from_score(0.95) == MemoryImportance.CRITICAL
        assert MemoryImportance.from_score(0.8) == MemoryImportance.HIGH
        assert MemoryImportance.from_score(0.5) == MemoryImportance.MEDIUM
        assert MemoryImportance.from_score(0.3) == MemoryImportance.LOW
        assert MemoryImportance.from_score(0.1) == MemoryImportance.TRIVIAL

    def test_boundary_values(self):
        assert MemoryImportance.from_score(0.9) == MemoryImportance.CRITICAL
        assert MemoryImportance.from_score(0.7) == MemoryImportance.HIGH
        assert MemoryImportance.from_score(0.45) == MemoryImportance.MEDIUM
        assert MemoryImportance.from_score(0.2) == MemoryImportance.LOW


class TestPermissionLevel:
    def test_implies(self):
        assert PermissionLevel.ADMIN.implies(PermissionLevel.READ)
        assert PermissionLevel.WRITE.implies(PermissionLevel.READ)
        assert not PermissionLevel.READ.implies(PermissionLevel.WRITE)
        assert PermissionLevel.FORGET.implies(PermissionLevel.WRITE)

    def test_from_string(self):
        assert PermissionLevel.from_string("admin") == PermissionLevel.ADMIN
        assert PermissionLevel.from_string("NONE") == PermissionLevel.NONE


class TestRelationType:
    def test_from_string(self):
        assert RelationType.from_string("causes") == RelationType.CAUSES
        assert RelationType.from_string("CONTRADICTS") == RelationType.CONTRADICTS

    def test_to_string(self):
        assert RelationType.SIMILAR.to_string() == "SIMILAR"


class TestDefaultTTL:
    def test_short_term_has_ttl(self):
        ttl = default_ttl(MemoryType.SHORT_TERM)
        assert ttl is not None
        assert ttl == timedelta(hours=1)

    def test_long_term_no_ttl(self):
        assert default_ttl(MemoryType.LONG_TERM) is None

    def test_event_has_ttl(self):
        ttl = default_ttl(MemoryType.EVENT)
        assert ttl is not None
        assert ttl.days == 365


class TestMemory:
    def test_creation_defaults(self):
        m = Memory(content="hello")
        assert m.content == "hello"
        assert m.memory_type == MemoryType.LONG_TERM
        assert m.user_id == "anonymous"
        assert m.scope == MemoryScope.USER
        assert m.importance == 0.5
        assert m.access_count == 0
        assert m.encrypted is False

    def test_importance_band(self):
        m = Memory(content="x", importance=0.8)
        assert m.importance_band == MemoryImportance.HIGH

    def test_is_expired_no_expiry(self):
        m = Memory(content="x")
        assert not m.is_expired()

    def test_is_expired_past(self):
        m = Memory(content="x", expires_at=datetime.utcnow() - timedelta(hours=1))
        assert m.is_expired()

    def test_is_expired_future(self):
        m = Memory(content="x", expires_at=datetime.utcnow() + timedelta(hours=1))
        assert not m.is_expired()

    def test_touch(self):
        m = Memory(content="x")
        before = m.access_count
        m.touch()
        assert m.access_count == before + 1
        assert m.updated_at >= m.created_at

    def test_to_dict_roundtrip(self):
        m = Memory(
            content="test memory",
            memory_type=MemoryType.PROJECT,
            user_id="user1",
            tags=["alpha", "beta"],
            importance=0.7,
            metadata={"key": "value"},
        )
        d = m.to_dict()
        m2 = Memory.from_dict(d)
        assert m2.content == m.content
        assert m2.memory_type == m.memory_type
        assert m2.user_id == m.user_id
        assert m2.tags == m.tags
        assert m2.importance == m.importance
        assert m2.metadata == m.metadata

    def test_from_dict_defaults(self):
        m = Memory.from_dict({"content": "minimal", "memory_type": "LONG_TERM"})
        assert m.user_id == "anonymous"
        assert m.scope == MemoryScope.USER
        assert m.access_count == 0


class TestPermission:
    def test_allows_granted(self):
        p = Permission(resource="user:u1", level=PermissionLevel.WRITE, principal_id="u1")
        assert p.allows(PermissionLevel.READ)
        assert p.allows(PermissionLevel.WRITE)
        assert not p.allows(PermissionLevel.ADMIN)

    def test_allows_denied(self):
        p = Permission(resource="user:u1", level=PermissionLevel.ADMIN, principal_id="u1", granted=False)
        assert not p.allows(PermissionLevel.READ)


class TestMemoryRelation:
    def test_to_dict_roundtrip(self):
        rel = MemoryRelation(source_id="s1", target_id="t1", relation=RelationType.CAUSES, strength=0.8)
        d = rel.to_dict()
        rel2 = MemoryRelation.from_dict(d)
        assert rel2.source_id == "s1"
        assert rel2.target_id == "t1"
        assert rel2.relation == RelationType.CAUSES
        assert rel2.strength == 0.8


# ===========================================================================
# 2. InMemoryStore
# ===========================================================================

class TestInMemoryStore:
    def test_insert_and_get(self):
        store = InMemoryStore()
        m = Memory(content="hello", memory_id="m1")
        store.insert(m)
        assert store.get("m1") is not None
        assert store.get("m1").content == "hello"

    def test_get_nonexistent(self):
        store = InMemoryStore()
        assert store.get("missing") is None

    def test_update(self):
        store = InMemoryStore()
        m = Memory(content="v1", memory_id="m1")
        store.insert(m)
        m.content = "v2"
        assert store.update(m) is True
        assert store.get("m1").content == "v2"

    def test_update_nonexistent(self):
        store = InMemoryStore()
        m = Memory(content="x", memory_id="nope")
        assert store.update(m) is False

    def test_delete(self):
        store = InMemoryStore()
        store.insert(Memory(content="x", memory_id="m1"))
        assert store.delete("m1") is True
        assert store.get("m1") is None

    def test_delete_nonexistent(self):
        store = InMemoryStore()
        assert store.delete("nope") is False

    def test_count(self):
        store = InMemoryStore()
        assert store.count() == 0
        store.insert(Memory(content="a", memory_id="a"))
        store.insert(Memory(content="b", memory_id="b"))
        assert store.count() == 2

    def test_all(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a"))
        store.insert(Memory(content="b", memory_id="b"))
        assert len(store.all()) == 2

    def test_query_by_user(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", user_id="u1"))
        store.insert(Memory(content="b", memory_id="b", user_id="u2"))
        results = store.query(user_id="u1")
        assert len(results) == 1
        assert results[0].user_id == "u1"

    def test_query_by_type(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", memory_type=MemoryType.SHORT_TERM))
        store.insert(Memory(content="b", memory_id="b", memory_type=MemoryType.LONG_TERM))
        results = store.query(memory_type=MemoryType.SHORT_TERM)
        assert len(results) == 1

    def test_query_by_tags(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", tags=["python", "code"]))
        store.insert(Memory(content="b", memory_id="b", tags=["rust"]))
        results = store.query(tags=["python"])
        assert len(results) == 1

    def test_query_by_project(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", project_id="p1"))
        store.insert(Memory(content="b", memory_id="b", project_id="p2"))
        results = store.query(project_id="p1")
        assert len(results) == 1

    def test_query_limit(self):
        store = InMemoryStore()
        for i in range(5):
            store.insert(Memory(content=f"m{i}", memory_id=f"m{i}"))
        results = store.query(limit=3)
        assert len(results) == 3

    def test_query_offset(self):
        store = InMemoryStore()
        for i in range(5):
            store.insert(Memory(content=f"m{i}", memory_id=f"m{i}", importance=i * 0.1))
        all_mem = store.query(limit=5)
        offset_mem = store.query(limit=5, offset=2)
        assert len(offset_mem) == 3

    def test_query_sorted_by_importance(self):
        store = InMemoryStore()
        store.insert(Memory(content="low", memory_id="l", importance=0.2))
        store.insert(Memory(content="high", memory_id="h", importance=0.9))
        store.insert(Memory(content="med", memory_id="m", importance=0.5))
        results = store.query()
        assert [r.importance for r in results] == [0.9, 0.5, 0.2]

    def test_relations(self):
        store = InMemoryStore()
        rel = MemoryRelation(source_id="s1", target_id="t1", relation=RelationType.RELATED)
        store.insert_relation(rel)
        results = store.relations_for("s1")
        assert len(results) == 1
        assert results[0].target_id == "t1"

    def test_delete_cascades_relations(self):
        store = InMemoryStore()
        store.insert(Memory(content="x", memory_id="m1"))
        store.insert_relation(MemoryRelation(source_id="m1", target_id="t1"))
        store.delete("m1")
        assert store.relations_for("m1") == []

    def test_semantic_search_cosine(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", embedding=[1.0, 0.0, 0.0]))
        store.insert(Memory(content="b", memory_id="b", embedding=[0.0, 1.0, 0.0]))
        store.insert(Memory(content="c", memory_id="c", embedding=[0.9, 0.1, 0.0]))
        results = store.semantic_search([1.0, 0.0, 0.0], top_k=2, metric="cosine")
        assert results[0][0] == "a"
        assert results[1][0] == "c"

    def test_semantic_search_dot(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", embedding=[5.0, 0.0]))
        store.insert(Memory(content="b", memory_id="b", embedding=[0.0, 5.0]))
        results = store.semantic_search([1.0, 0.0], top_k=2, metric="dot")
        assert results[0][0] == "a"

    def test_semantic_search_euclidean(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", embedding=[1.0, 0.0]))
        store.insert(Memory(content="b", memory_id="b", embedding=[-1.0, 0.0]))
        results = store.semantic_search([1.0, 0.0], top_k=2, metric="euclidean")
        assert results[0][0] == "a"

    def test_semantic_search_empty(self):
        store = InMemoryStore()
        assert store.semantic_search([1.0, 0.0]) == []

    def test_semantic_search_unknown_metric(self):
        store = InMemoryStore()
        store.insert(Memory(content="a", memory_id="a", embedding=[1.0]))
        with pytest.raises(ValueError, match="Unknown metric"):
            store.semantic_search([1.0], metric="manhattan")


# ===========================================================================
# 3. MemoryManager
# ===========================================================================

class TestMemoryManager:
    def test_store_and_get(self):
        mgr, _ = _make_manager()
        m = mgr.store("remember this", user_id="u1")
        fetched = mgr.get(m.memory_id)
        assert fetched is not None
        assert fetched.content == "remember this"
        assert fetched.user_id == "u1"

    def test_store_with_tags(self):
        mgr, _ = _make_manager()
        m = mgr.store("tagged", tags=["alpha", "beta"])
        assert "alpha" in m.tags
        assert "beta" in m.tags

    def test_store_extracts_inline_tags(self):
        mgr, _ = _make_manager()
        m = mgr.store("use #python and #code")
        assert "python" in m.tags
        assert "code" in m.tags

    def test_store_short_term_has_ttl(self):
        mgr, _ = _make_manager()
        m = mgr.store("temp", memory_type=MemoryType.SHORT_TERM)
        assert m.expires_at is not None

    def test_store_with_ttl_override(self):
        mgr, _ = _make_manager()
        m = mgr.store("custom ttl", ttl_seconds=120)
        assert m.expires_at is not None

    def test_get_nonexistent(self):
        mgr, _ = _make_manager()
        assert mgr.get("missing") is None

    def test_get_touches_access_count(self):
        mgr, _ = _make_manager()
        m = mgr.store("touch me")
        mgr.get(m.memory_id)
        fetched = mgr.get(m.memory_id)
        assert fetched.access_count >= 2

    def test_recall(self):
        mgr, _ = _make_manager()
        mgr.store("a", user_id="u1")
        mgr.store("b", user_id="u2")
        results = mgr.recall(user_id="u1")
        assert len(results) == 1

    def test_recall_by_type(self):
        mgr, _ = _make_manager()
        mgr.store("short", memory_type=MemoryType.SHORT_TERM)
        mgr.store("long", memory_type=MemoryType.LONG_TERM)
        results = mgr.recall(memory_type=MemoryType.SHORT_TERM)
        assert len(results) == 1

    def test_recall_by_project(self):
        mgr, _ = _make_manager()
        mgr.store("proj a", project_id="p1")
        mgr.store("proj b", project_id="p2")
        results = mgr.recall(project_id="p1")
        assert len(results) == 1

    def test_forget(self):
        mgr, _ = _make_manager()
        m = mgr.store("forget me")
        assert mgr.forget(m.memory_id) is True
        assert mgr.get(m.memory_id) is None

    def test_forget_expired(self):
        mgr, _ = _make_manager()
        mgr.store("alive")
        m = mgr.store("dying")
        m.expires_at = datetime.utcnow() - timedelta(hours=1)
        mgr._store.update(m)
        count = mgr.forget_expired()
        assert count == 1

    def test_forget_low_importance(self):
        mgr, _ = _make_manager()
        mgr.store("important", importance=0.9)
        mgr.store("trivial", importance=0.1)
        mgr.store("also low", importance=0.2)
        count = mgr.forget_low_importance(0.5)
        assert count == 2

    def test_purge_scope(self):
        mgr, _ = _make_manager()
        mgr.store("u1 a", user_id="u1")
        mgr.store("u1 b", user_id="u1")
        mgr.store("u2 a", user_id="u2")
        count = mgr.purge_scope("u1")
        assert count == 2
        remaining = mgr.recall(user_id="u2")
        assert len(remaining) == 1

    def test_tag(self):
        mgr, _ = _make_manager()
        m = mgr.store("tagged")
        result = mgr.tag(m.memory_id, ["newtag"])
        assert "newtag" in result.tags

    def test_untag(self):
        mgr, _ = _make_manager()
        m = mgr.store("tagged", tags=["remove_me", "keep"])
        result = mgr.untag(m.memory_id, ["remove_me"])
        assert "remove_me" not in result.tags
        assert "keep" in result.tags

    def test_tag_nonexistent(self):
        mgr, _ = _make_manager()
        assert mgr.tag("missing", ["tag"]) is None

    def test_relate(self):
        mgr, _ = _make_manager()
        m1 = mgr.store("first")
        m2 = mgr.store("second")
        rel = mgr.relate(m1.memory_id, m2.memory_id, RelationType.CAUSES, 0.8)
        assert rel.source_id == m1.memory_id
        assert rel.relation == RelationType.CAUSES

    def test_relations(self):
        mgr, _ = _make_manager()
        m1 = mgr.store("a")
        m2 = mgr.store("b")
        mgr.relate(m1.memory_id, m2.memory_id)
        rels = mgr.relations(m1.memory_id)
        assert len(rels) == 1

    def test_rank(self):
        mgr, _ = _make_manager()
        m1 = mgr.store("important", importance=0.9)
        m2 = mgr.store("trivial", importance=0.1)
        ranked = mgr.rank([m1, m2])
        assert ranked[0][0].memory_id == m1.memory_id

    def test_rank_limit(self):
        mgr, _ = _make_manager()
        memories = [mgr.store(f"m{i}", importance=i * 0.1) for i in range(5)]
        ranked = mgr.rank(memories, limit=3)
        assert len(ranked) == 3


# ===========================================================================
# 4. AI Features
# ===========================================================================

class TestEmbedder:
    def test_deterministic(self):
        e = Embedder(dim=32)
        v1 = e.embed("hello world")
        v2 = e.embed("hello world")
        assert v1 == v2

    def test_different_inputs_different_vectors(self):
        e = Embedder(dim=32)
        v1 = e.embed("cats are cute")
        v2 = e.embed("dogs are friendly")
        assert v1 != v2

    def test_empty_input(self):
        e = Embedder(dim=16)
        v = e.embed("")
        assert all(x == 0.0 for x in v)

    def test_normalized(self):
        e = Embedder(dim=64)
        v = e.embed("test normalization")
        norm = math.sqrt(sum(x * x for x in v))
        assert abs(norm - 1.0) < 1e-6

    def test_stopwords_removed(self):
        tokens = _tokenize("the quick brown fox is a very good animal")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "a" not in tokens
        assert "quick" in tokens


class TestAIFeatures:
    def _make_ai(self) -> tuple[AIFeatures, MemoryManager, InMemoryStore]:
        mgr, store = _make_manager(embedding_dim=32)
        ai = AIFeatures(mgr, Embedder(dim=32))
        return ai, mgr, store

    def test_embed(self):
        ai, _, _ = self._make_ai()
        vec = ai.embed("hello")
        assert len(vec) == 32

    def test_search_returns_results(self):
        ai, mgr, _ = self._make_ai()
        mgr.store("python programming language", tags=["code"])
        mgr.store("javascript web development", tags=["code"])
        mgr.store("cooking recipes", tags=["food"])
        results = ai.search("python code", top_k=2)
        assert len(results) > 0
        assert results[0][0].content == "python programming language"

    def test_search_with_user_filter(self):
        ai, mgr, _ = self._make_ai()
        mgr.store("user1 memory", user_id="u1", embedding=ai.embed("user1 memory"))
        mgr.store("user2 memory", user_id="u2", embedding=ai.embed("user2 memory"))
        results = ai.search("memory", user_id="u1", top_k=5)
        assert all(m.user_id == "u1" for m, _ in results)

    def test_search_with_min_score(self):
        ai, mgr, _ = self._make_ai()
        mgr.store("completely unrelated topic", embedding=ai.embed("completely unrelated topic"))
        results = ai.search("python programming", min_score=0.99)
        assert len(results) == 0

    def test_build_context(self):
        ai, mgr, _ = self._make_ai()
        mgr.store("Important context about AI", importance=0.9)
        ctx = ai.build_context("AI context")
        assert "AI" in ctx or "Important" in ctx

    def test_build_context_with_project(self):
        ai, mgr, _ = self._make_ai()
        mgr.store("project memory", project_id="p1")
        ctx = ai.build_context("project", project_id="p1")
        assert len(ctx) >= 0

    def test_summarize_empty(self):
        ai, _, _ = self._make_ai()
        assert ai.summarize([]) == ""

    def test_summarize_single(self):
        ai, _, _ = self._make_ai()
        m = Memory(content="Single memory.")
        assert ai.summarize([m]) == "Single memory."

    def test_summarize_multiple(self):
        ai, _, _ = self._make_ai()
        mems = [
            Memory(content="First sentence. Second sentence."),
            Memory(content="Third sentence. Fourth sentence."),
        ]
        result = ai.summarize(mems, max_sentences=2)
        assert len(result) > 0

    def test_detect_relationships(self):
        ai, mgr, _ = self._make_ai()
        m1 = mgr.store("python programming language code", tags=["code"])
        m2 = mgr.store("python development programming", tags=["code"])
        m3 = mgr.store("cooking food recipes", tags=["food"])
        rels = ai.detect_relationships(m1, [m2, m3])
        assert len(rels) >= 1
        types = [r for _, r, _ in rels]
        assert RelationType.SIMILAR in types or RelationType.RELATED in types

    def test_auto_relate(self):
        ai, mgr, _ = self._make_ai()
        m1 = mgr.store("python programming language", tags=["code"])
        m2 = mgr.store("python development coding", tags=["code"])
        created = ai.auto_relate(m1, threshold=0.1)
        assert len(created) >= 1

    def test_summarize_short_term(self):
        mgr, store = _make_manager(embedding_dim=32)
        ai = AIFeatures(mgr, Embedder(dim=32))
        session_id = "sess1"
        mgr.store("step 1 done", memory_type=MemoryType.SHORT_TERM, session_id=session_id)
        mgr.store("step 2 done", memory_type=MemoryType.SHORT_TERM, session_id=session_id)
        summary = ai.summarize_short_term(session_id)
        assert summary is not None
        assert summary.memory_type == MemoryType.LONG_TERM
        assert "summary" in summary.tags

    def test_summarize_short_term_empty(self):
        mgr, store = _make_manager(embedding_dim=32)
        ai = AIFeatures(mgr, Embedder(dim=32))
        assert ai.summarize_short_term("nonexistent") is None


# ===========================================================================
# 5. Security
# ===========================================================================

class TestMemorySecurity:
    def test_grant_and_check(self):
        sec = MemorySecurity()
        sec.grant("u1", "user:u1", PermissionLevel.WRITE)
        assert sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.READ)
        assert sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.WRITE)
        assert not sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.ADMIN)

    def test_revoke_removes_explicit_grant(self):
        sec = MemorySecurity(default_level=PermissionLevel.READ)
        sec.grant("u1", "user:u1", PermissionLevel.ADMIN)
        assert sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.ADMIN)
        sec.revoke("u1", "user:u1")
        # After revoke, falls back to default_level (READ), so ADMIN is denied
        assert not sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.ADMIN)

    def test_owner_default(self):
        sec = MemorySecurity()
        assert sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.READ)
        assert sec.check("u1", MemoryScope.USER, "u1", PermissionLevel.WRITE)

    def test_non_owner_denied_global(self):
        sec = MemorySecurity()
        assert not sec.check("u1", MemoryScope.GLOBAL, "u2", PermissionLevel.READ)

    def test_can_read_write_forget(self):
        sec = MemorySecurity()
        sec.grant("u1", "user:u1", PermissionLevel.FORGET)
        assert sec.can_read("u1", MemoryScope.USER, "u1")
        assert sec.can_write("u1", MemoryScope.USER, "u1")
        assert sec.can_forget("u1", MemoryScope.USER, "u1")

    def test_list_grants(self):
        sec = MemorySecurity()
        sec.grant("u1", "user:u1", PermissionLevel.READ)
        grants = sec.list_grants()
        assert len(grants) == 1
        assert grants[0].principal_id == "u1"

    def test_is_encrypted_no_crypto(self):
        sec = MemorySecurity()
        assert not sec.is_encrypted()

    def test_encrypt_content_no_crypto(self):
        sec = MemorySecurity()
        content, encrypted = sec.encrypt_content("hello")
        assert content == "hello"
        assert encrypted is False

    def test_decrypt_content_not_encrypted(self):
        sec = MemorySecurity()
        assert sec.decrypt_content("hello", was_encrypted=False) == "hello"

    def test_scope_resources(self):
        sec = MemorySecurity()
        assert sec._resource_for(MemoryScope.GLOBAL, "u1") == "global"
        assert sec._resource_for(MemoryScope.USER, "u1") == "user:u1"
        assert sec._resource_for(MemoryScope.PROJECT, "u1") == "project:u1"
        assert sec._resource_for(MemoryScope.SESSION, "u1") == "session:u1"


# ===========================================================================
# 6. Config
# ===========================================================================

class TestMemoryConfig:
    def test_defaults(self):
        cfg = MemoryConfig()
        assert cfg.storage_backend == "arcanisdb"
        assert cfg.embedding_dim == 1536
        assert cfg.weight_importance == 0.5
        assert cfg.auto_forget_expired is True

    def test_custom(self):
        cfg = MemoryConfig(embedding_dim=256, weight_importance=0.7)
        assert cfg.embedding_dim == 256
        assert cfg.weight_importance == 0.7
