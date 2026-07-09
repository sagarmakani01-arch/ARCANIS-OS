"""Embedding engine for semantic file understanding.

Generates vector embeddings from file content and metadata
for semantic search and organization.
"""

import hashlib
import math
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class FileEmbedding:
    """Represents a file's semantic embedding."""

    inode_id: uuid.UUID
    vector: List[float] = field(default_factory=list)
    text_features: Dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    content_hash: str = ""
    embedding_version: str = "1.0"

    def similarity(self, other: "FileEmbedding") -> float:
        if not self.vector or not other.vector:
            return 0.0
        if len(self.vector) != len(other.vector):
            return 0.0

        dot_product = sum(a * b for a, b in zip(self.vector, other.vector))
        norm_a = math.sqrt(sum(a * a for a in self.vector))
        norm_b = math.sqrt(sum(b * b for b in other.vector))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def to_dict(self) -> dict:
        return {
            "inode_id": str(self.inode_id),
            "vector_dim": len(self.vector),
            "features": self.text_features,
            "created": self.created_at,
            "content_hash": self.content_hash,
        }


class EmbeddingEngine:
    """Generates embeddings from file content and metadata."""

    VOCAB_SIZE = 10000
    EMBEDDING_DIM = 128

    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "between", "out", "off", "over", "under", "again", "further", "then",
        "once", "and", "but", "or", "nor", "not", "so", "very", "just",
    }

    def __init__(self, embedding_dim: int = EMBEDDING_DIM):
        self.embedding_dim = embedding_dim
        self._vocabulary: Dict[str, int] = {}
        self._idf_scores: Dict[str, float] = {}
        self._document_count = 0
        self._word_freq: Dict[str, int] = {}
        self._embeddings: Dict[uuid.UUID, FileEmbedding] = {}

    def generate_embedding(self, inode_id: uuid.UUID, content: bytes, metadata: Optional[Dict] = None) -> FileEmbedding:
        text = self._extract_text(content, metadata)
        tokens = self._tokenize(text)
        tf_scores = self._compute_tf(tokens)

        vector = self._compute_embedding_vector(tf_scores)
        text_features = self._extract_features(tokens, content)

        content_hash = hashlib.sha256(content).hexdigest()[:16]

        embedding = FileEmbedding(
            inode_id=inode_id,
            vector=vector,
            text_features=text_features,
            content_hash=content_hash,
        )

        self._embeddings[inode_id] = embedding
        self._update_idf(tokens)

        return embedding

    def get_embedding(self, inode_id: uuid.UUID) -> Optional[FileEmbedding]:
        return self._embeddings.get(inode_id)

    def remove_embedding(self, inode_id: uuid.UUID) -> bool:
        if inode_id in self._embeddings:
            del self._embeddings[inode_id]
            return True
        return False

    def find_similar(self, query_vector: List[float], top_k: int = 10) -> List[Tuple[uuid.UUID, float]]:
        similarities = []
        for inode_id, embedding in self._embeddings.items():
            sim = self._cosine_similarity(query_vector, embedding.vector)
            similarities.append((inode_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def find_similar_to_file(self, inode_id: uuid.UUID, top_k: int = 10) -> List[Tuple[uuid.UUID, float]]:
        source = self._embeddings.get(inode_id)
        if not source:
            return []
        return self.find_similar(source.vector, top_k)

    def _extract_text(self, content: bytes, metadata: Optional[Dict] = None) -> str:
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

        if metadata:
            for key in ["name", "description", "tags", "author", "mime_type"]:
                if key in metadata:
                    text += f" {metadata[key]}"

        return text.lower()

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r"[a-z0-9]+", text)
        return [w for w in words if w not in self.STOP_WORDS and len(w) > 2]

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        if not tokens:
            return {}

        counter = Counter(tokens)
        max_freq = max(counter.values()) if counter else 1

        return {word: freq / max_freq for word, freq in counter.items()}

    def _compute_embedding_vector(self, tf_scores: Dict[str, float]) -> List[float]:
        vector = [0.0] * self.embedding_dim

        for word, tf in tf_scores.items():
            word_hash = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            idf = self._idf_scores.get(word, 1.0)

            idx = word_hash % self.embedding_dim
            vector[idx] += tf * idf

            for i in range(1, 4):
                idx2 = (word_hash + i * 7) % self.embedding_dim
                vector[idx2] += tf * idf * (0.5 ** i)

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    def _extract_features(self, tokens: List[str], content: bytes) -> Dict[str, float]:
        features = {}

        features["token_count"] = len(tokens)
        features["unique_tokens"] = len(set(tokens))
        features["content_size"] = len(content)
        features["avg_token_length"] = sum(len(t) for t in tokens) / max(len(tokens), 1)

        if tokens:
            counter = Counter(tokens)
            features["lexical_diversity"] = len(set(tokens)) / len(tokens)
            features["top_word_freq"] = counter.most_common(1)[0][1] / len(tokens)
        else:
            features["lexical_diversity"] = 0
            features["top_word_freq"] = 0

        return features

    def _update_idf(self, tokens: List[str]) -> None:
        self._document_count += 1
        unique_tokens = set(tokens)

        for token in unique_tokens:
            self._word_freq[token] = self._word_freq.get(token, 0) + 1

        for token, freq in self._word_freq.items():
            self._idf_scores[token] = math.log(self._document_count / (1 + freq))

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def get_vocabulary_size(self) -> int:
        return len(self._vocabulary)

    def get_embedding_count(self) -> int:
        return len(self._embeddings)

    def get_info(self) -> dict:
        return {
            "embedding_dim": self.embedding_dim,
            "total_embeddings": len(self._embeddings),
            "vocabulary_size": len(self._word_freq),
            "document_count": self._document_count,
        }
