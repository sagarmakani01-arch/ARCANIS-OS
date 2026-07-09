"""Semantic search engine for ArcanisFileSystem.

Combines keyword and vector-based search for intelligent file retrieval.
"""

import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class SearchMode(Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    FUZZY = "fuzzy"
    REGEX = "regex"


class SearchScope(Enum):
    ALL = "all"
    FILES = "files"
    DIRECTORIES = "directories"
    CURRENT_DIR = "current_dir"


@dataclass
class SearchResult:
    """Represents a single search result."""

    inode_id: uuid.UUID
    path: str
    score: float = 0.0
    match_type: str = ""
    match_details: Dict = field(default_factory=dict)
    snippet: str = ""

    def to_dict(self) -> dict:
        return {
            "inode_id": str(self.inode_id),
            "path": self.path,
            "score": self.score,
            "match_type": self.match_type,
            "details": self.match_details,
            "snippet": self.snippet,
        }


@dataclass
class SearchQuery:
    """Represents a search query with options."""

    text: str
    mode: SearchMode = SearchMode.HYBRID
    scope: SearchScope = SearchScope.ALL
    max_results: int = 100
    min_score: float = 0.1
    case_sensitive: bool = False
    file_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    date_from: Optional[float] = None
    date_to: Optional[float] = None
    size_min: Optional[int] = None
    size_max: Optional[int] = None


class SemanticSearch:
    """Provides intelligent search across the filesystem."""

    MAX_RESULTS = 10000

    def __init__(self, embedding_engine=None, indexer=None):
        self._embedding_engine = embedding_engine
        self._indexer = indexer
        self._search_history: List[Tuple[SearchQuery, List[SearchResult]]] = []
        self._query_suggestions: Dict[str, int] = {}

    def search(self, query: SearchQuery) -> List[SearchResult]:
        results = []

        if query.mode in (SearchMode.KEYWORD, SearchMode.HYBRID):
            keyword_results = self._keyword_search(query)
            results.extend(keyword_results)

        if query.mode in (SearchMode.SEMANTIC, SearchMode.HYBRID) and self._embedding_engine:
            semantic_results = self._semantic_search(query)
            for sr in semantic_results:
                existing = next((r for r in results if r.inode_id == sr.inode_id), None)
                if existing:
                    existing.score = max(existing.score, sr.score)
                    existing.match_type = "hybrid"
                else:
                    results.append(sr)

        if query.mode == SearchMode.FUZZY:
            fuzzy_results = self._fuzzy_search(query)
            results.extend(fuzzy_results)

        if query.mode == SearchMode.REGEX:
            regex_results = self._regex_search(query)
            results.extend(regex_results)

        results = self._apply_filters(results, query)
        results.sort(key=lambda r: r.score, reverse=True)
        results = results[:query.max_results]

        self._search_history.append((query, results))
        if len(self._search_history) > 100:
            self._search_history.pop(0)

        self._update_suggestions(query.text)

        return results

    def quick_search(self, text: str, max_results: int = 10) -> List[SearchResult]:
        query = SearchQuery(text=text, mode=SearchMode.KEYWORD, max_results=max_results)
        return self.search(query)

    def find_by_path(self, path_pattern: str) -> List[SearchResult]:
        import fnmatch
        results = []

        if self._indexer:
            for entry in self._indexer.get_all_entries():
                if fnmatch.fnmatch(entry.path, path_pattern):
                    results.append(SearchResult(
                        inode_id=entry.inode_id,
                        path=entry.path,
                        score=1.0,
                        match_type="path_pattern",
                    ))

        return results

    def find_similar(self, inode_id: uuid.UUID, top_k: int = 10) -> List[SearchResult]:
        if not self._embedding_engine:
            return []

        similar = self._embedding_engine.find_similar_to_file(inode_id, top_k)
        results = []

        for sim_id, score in similar:
            entry = self._indexer.get_entry(sim_id) if self._indexer else None
            path = entry.path if entry else str(sim_id)
            results.append(SearchResult(
                inode_id=sim_id,
                path=path,
                score=score,
                match_type="semantic_similarity",
            ))

        return results

    def suggest(self, partial: str, max_suggestions: int = 5) -> List[str]:
        suggestions = []
        partial_lower = partial.lower()

        for query_text, count in self._query_suggestions.items():
            if partial_lower in query_text.lower():
                suggestions.append((query_text, count))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in suggestions[:max_suggestions]]

    def get_popular_queries(self, top_k: int = 10) -> List[str]:
        sorted_queries = sorted(self._query_suggestions.items(), key=lambda x: x[1], reverse=True)
        return [q[0] for q in sorted_queries[:top_k]]

    def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        results = []
        keywords = self._tokenize(query.text)

        if not self._indexer:
            return results

        index_results = self._indexer.search_keywords(keywords, match_all=False)

        for entry in index_results:
            score = self._calculate_keyword_score(entry, keywords)
            if score >= query.min_score:
                snippet = self._generate_snippet(entry, keywords)
                results.append(SearchResult(
                    inode_id=entry.inode_id,
                    path=entry.path,
                    score=score,
                    match_type="keyword",
                    match_details={"keywords": keywords},
                    snippet=snippet,
                ))

        return results

    def _semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        results = []
        keywords = self._tokenize(query.text)

        if not keywords or not self._embedding_engine:
            return results

        query_vector = self._create_query_vector(keywords)
        similar = self._embedding_engine.find_similar(query_vector, query.max_results)

        for inode_id, score in similar:
            if score >= query.min_score:
                entry = self._indexer.get_entry(inode_id) if self._indexer else None
                path = entry.path if entry else str(inode_id)
                results.append(SearchResult(
                    inode_id=inode_id,
                    path=path,
                    score=score,
                    match_type="semantic",
                ))

        return results

    def _fuzzy_search(self, query: SearchQuery) -> List[SearchResult]:
        results = []
        query_lower = query.text.lower()

        if not self._indexer:
            return results

        for entry in self._indexer.get_all_entries():
            path_lower = entry.path.lower()
            distance = self._levenshtein_distance(query_lower, path_lower)
            max_len = max(len(query_lower), len(path_lower))

            if max_len > 0:
                similarity = 1.0 - (distance / max_len)
                if similarity > 0.6:
                    results.append(SearchResult(
                        inode_id=entry.inode_id,
                        path=entry.path,
                        score=similarity,
                        match_type="fuzzy",
                        match_details={"distance": distance},
                    ))

        return results

    def _regex_search(self, query: SearchQuery) -> List[SearchResult]:
        results = []

        try:
            pattern = re.compile(query.text, 0 if query.case_sensitive else re.IGNORECASE)
        except re.error:
            return results

        if not self._indexer:
            return results

        for entry in self._indexer.get_all_entries():
            match = pattern.search(entry.path)
            if match:
                results.append(SearchResult(
                    inode_id=entry.inode_id,
                    path=entry.path,
                    score=1.0,
                    match_type="regex",
                    match_details={"match": match.group()},
                ))

        return results

    def _apply_filters(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        filtered = []

        for result in results:
            if query.exclude_patterns:
                import fnmatch
                excluded = False
                for pattern in query.exclude_patterns:
                    if fnmatch.fnmatch(result.path, pattern):
                        excluded = True
                        break
                if excluded:
                    continue

            if query.file_patterns:
                import fnmatch
                matched = False
                for pattern in query.file_patterns:
                    if fnmatch.fnmatch(result.path, pattern):
                        matched = True
                        break
                if not matched:
                    continue

            filtered.append(result)

        return filtered

    def _tokenize(self, text: str) -> List[str]:
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                       "to", "of", "in", "for", "on", "with", "at", "by", "from"}
        words = re.findall(r"[a-z0-9]+", text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]

    def _calculate_keyword_score(self, entry, keywords: List[str]) -> float:
        matching = sum(1 for kw in keywords if kw in entry.keywords)
        return matching / max(len(keywords), 1)

    def _generate_snippet(self, entry, keywords: List[str], max_len: int = 200) -> str:
        text = " ".join(entry.keywords[:50])
        for kw in keywords:
            idx = text.lower().find(kw)
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(text), idx + len(kw) + 50)
                return text[start:end]
        return text[:max_len]

    def _create_query_vector(self, keywords: List[str]) -> List[float]:
        import hashlib
        vector = [0.0] * 128
        for kw in keywords:
            h = int(hashlib.md5(kw.encode()).hexdigest()[:8], 16)
            idx = h % 128
            vector[idx] += 1.0
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    def _update_suggestions(self, query_text: str) -> None:
        normalized = query_text.lower().strip()
        self._query_suggestions[normalized] = self._query_suggestions.get(normalized, 0) + 1

    def get_search_stats(self) -> dict:
        return {
            "total_searches": len(self._search_history),
            "unique_queries": len(self._query_suggestions),
            "has_embedding_engine": self._embedding_engine is not None,
            "has_indexer": self._indexer is not None,
        }
