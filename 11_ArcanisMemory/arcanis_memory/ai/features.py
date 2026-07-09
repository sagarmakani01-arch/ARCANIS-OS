"""AI features for ArcanisMemory.

This module provides semantic search, context building, memory summarization,
and relationship detection. Embeddings are produced by a pluggable
:class:`Embedder`; when ArcanisDatabase is available its embedding store is used
for vector search, otherwise a local cosine similarity fallback runs over an
in-memory store.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Optional

import numpy as np

from arcanis_memory.core.manager import MemoryManager
from arcanis_memory.core.types import Memory, MemoryID, RelationType


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "for", "of",
    "to", "in", "on", "at", "by", "with", "as", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "it", "its", "from", "can", "will",
    "would", "should", "could", "do", "does", "did", "have", "has", "had",
}


class Embedder:
    """Strategy for turning text into a fixed-dimension vector.

    The default :class:`HashingEmbedder` is deterministic and dependency-free so
    the memory layer works without a model provider. Production deployments can
    substitute an embedder backed by ArcanisDatabase's embedding model.
    """

    def __init__(self, dim: int = 1536) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float64)
        tokens = _tokenize(text)
        if not tokens:
            return vec.tolist()
        for tok in tokens:
            h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) & 1 else -1.0
            vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


class AIFeatures:
    """Semantic search, context building, summarization, and relation detection."""

    def __init__(self, manager: MemoryManager, embedder: Optional[Embedder] = None):
        self.manager = manager
        self.embedder = embedder or Embedder(manager.config.embedding_dim)
        self._db = getattr(manager.store, "db", None)

    # --- Semantic search -------------------------------------------------------

    def embed(self, text: str) -> list[float]:
        return self.embedder.embed(text)

    def search(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        memory_type=None,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[tuple[Memory, float]]:
        query_vec = self.embed(query)

        # Prefer the database vector store when available.
        if self._db is not None:
            try:
                results = self._db.embeddings.search(
                    "memories", query_vec, top_k=top_k * 3
                )
                scored: list[tuple[Memory, float]] = []
                for r in results:
                    mid = r.get("metadata", {}).get("memory_id")
                    if not mid:
                        continue
                    mem = self.manager.store.get(mid)
                    if mem is None:
                        continue
                    if user_id is not None and mem.user_id != user_id:
                        continue
                    if memory_type is not None and mem.memory_type != memory_type:
                        continue
                    scored.append((mem, float(r["score"])))
                scored = [(m, s) for m, s in scored if s >= min_score]
                return scored[:top_k]
            except Exception:
                pass

        # Local fallback for in-memory stores.
        from arcanis_memory.storage.memory_store import InMemoryStore

        if isinstance(self.manager.store, InMemoryStore):
            hits = self.manager.store.semantic_search(query_vec, top_k=top_k * 3)
            scored = []
            for mid, score in hits:
                mem = self.manager.store.get(mid)
                if mem is None:
                    continue
                if user_id is not None and mem.user_id != user_id:
                    continue
                if memory_type is not None and mem.memory_type != memory_type:
                    continue
                scored.append((mem, score))
            return [(m, s) for m, s in scored if s >= min_score][:top_k]

        # No vectors stored: fall back to keyword overlap ranking.
        return self._keyword_search(query, user_id=user_id, memory_type=memory_type, top_k=top_k)

    def _keyword_search(self, query: str, *, user_id=None, memory_type=None, top_k: int = 5):
        q_tokens = set(_tokenize(query))
        memories = self.manager.recall(
            user_id=user_id, memory_type=memory_type, limit=10_000
        )
        scored = []
        for m in memories:
            m_tokens = set(_tokenize(m.content))
            if not q_tokens or not m_tokens:
                continue
            overlap = len(q_tokens & m_tokens) / len(q_tokens | m_tokens)
            if overlap > 0:
                scored.append((m, float(overlap)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # --- Context building ------------------------------------------------------

    def build_context(
        self,
        query: str,
        *,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        max_memories: int = 10,
        max_tokens: int = 4000,
    ) -> str:
        if project_id is not None:
            proj_memories = self.manager.recall(
                user_id=user_id, project_id=project_id, limit=max_memories
            )
        else:
            proj_memories = []
        semantic = self.search(query, user_id=user_id, top_k=max_memories)
        ranked = self.manager.rank([m for m, _ in semantic] + proj_memories)
        selected = [m for m, _ in ranked[:max_memories]]

        lines = []
        used = 0
        for m in selected:
            line = f"- [{m.memory_type.to_string()}] {m.content}"
            used += len(line) // 4
            if used > max_tokens:
                break
            lines.append(line)
        return "\n".join(lines)

    # --- Memory summarization --------------------------------------------------

    def summarize(self, memories: list[Memory], max_sentences: int = 3) -> str:
        if not memories:
            return ""
        if len(memories) == 1:
            return memories[0].content
        sentences: list[str] = []
        for m in memories:
            sentences.extend(re.split(r"(?<=[.!?])\s+", m.content.strip()))
        sentences = [s for s in sentences if s]
        if len(sentences) <= max_sentences:
            return " ".join(sentences)
        scored = self._rank_sentences(sentences)
        top = [s for s, _ in scored[:max_sentences]]
        return " ".join(top)

    def _rank_sentences(self, sentences: list[str]) -> list[tuple[str, float]]:
        freq: Counter[str] = Counter()
        for s in sentences:
            freq.update(set(_tokenize(s)))
        scored = []
        for s in sentences:
            words = _tokenize(s)
            score = sum(freq.get(w, 0) for w in words) / max(1, len(words))
            scored.append((s, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def summarize_short_term(self, session_id: str) -> Optional[Memory]:
        memories = self.manager.recall(
            memory_type=__import__(
                "arcanis_memory.core.types", fromlist=["MemoryType"]
            ).MemoryType.SHORT_TERM,
            limit=10_000,
        )
        memories = [m for m in memories if m.session_id == session_id]
        if not memories:
            return None
        summary = self.summarize(memories)
        from arcanis_memory.core.types import MemoryType, MemoryScope

        return self.manager.store(
            content=summary,
            memory_type=MemoryType.LONG_TERM,
            session_id=session_id,
            tags=["summary", "short_term"],
            importance=max(m.importance for m in memories),
        )

    # --- Relationship detection ------------------------------------------------

    def detect_relationships(
        self, memory: Memory, candidates: Optional[list[Memory]] = None
    ) -> list[tuple[Memory, RelationType, float]]:
        if candidates is None:
            candidates = self.manager.recall(user_id=memory.user_id, limit=10_000)
        relations = []
        m_tokens = set(_tokenize(memory.content))
        for other in candidates:
            if other.memory_id == memory.memory_id:
                continue
            o_tokens = set(_tokenize(other.content))
            if not m_tokens or not o_tokens:
                continue
            overlap = len(m_tokens & o_tokens) / len(m_tokens | o_tokens)
            if overlap < 0.15:
                continue
            if memory.tags and other.tags and set(memory.tags) & set(other.tags):
                relation = RelationType.SIMILAR
                strength = min(1.0, overlap + 0.2)
            else:
                relation = RelationType.RELATED
                strength = overlap
            relations.append((other, relation, round(strength, 4)))
        relations.sort(key=lambda x: x[2], reverse=True)
        return relations

    def auto_relate(
        self, memory: Memory, threshold: float = 0.3
    ) -> list[MemoryRelation]:
        from arcanis_memory.core.types import MemoryRelation

        created = []
        for other, relation, strength in self.detect_relationships(memory):
            if strength >= threshold:
                rel = self.manager.relate(
                    memory.memory_id, other.memory_id, relation, strength
                )
                created.append(rel)
        return created
