from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .config import SemanticFSConfig
from .storage import FileEntity, MetadataStore
from .indexer import EmbeddingIndex, SemanticIndexer


@dataclass
class SearchResult:
    file: FileEntity
    score: float
    match_type: str = "semantic"


@dataclass
class OrganizationSuggestion:
    current_files: int
    current_folders: int
    suggested_structure: dict[str, Any]
    confidence: float
    rationale: str


class SemanticFSEngine:
    def __init__(self, config: Optional[SemanticFSConfig] = None):
        self.config = config or SemanticFSConfig()
        self.store = MetadataStore(self.config.db_path)
        self.embedding_index = EmbeddingIndex(dim=self.config.embedding_dim)
        self.indexer = SemanticIndexer(self.store, self.embedding_index)
        self._embedding_model = None

    def initialize(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer(self.config.embedding_model)
        except ImportError:
            self._embedding_model = None

    def index_file(self, path: Path) -> Optional[FileEntity]:
        return self.indexer.index_file(path, self._embedding_model)

    def index_directory(self, path: Optional[Path] = None) -> list[FileEntity]:
        target = path or self.config.root_path
        return self.indexer.index_directory(target, self._embedding_model)

    def search(self, query: str, limit: Optional[int] = None) -> list[SearchResult]:
        limit = limit or self.config.max_search_results
        results: list[SearchResult] = []

        keyword_results = self.store.search_files(query, limit=limit)
        for entity in keyword_results:
            results.append(SearchResult(file=entity, score=0.5, match_type="keyword"))

        if self._embedding_model:
            try:
                query_embedding = self._embedding_model.encode(query).tolist()
                semantic_matches = self.embedding_index.search(query_embedding, top_k=limit)
                for file_id, score in semantic_matches:
                    entity = self.store.get_file(file_id)
                    if entity and score >= self.config.similarity_threshold:
                        if not any(r.file.id == file_id for r in results):
                            results.append(SearchResult(file=entity, score=score, match_type="semantic"))
            except Exception:
                pass

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def search_similar(self, file_id: str, top_k: int = 10) -> list[SearchResult]:
        entity = self.store.get_file(file_id)
        if not entity or not entity.embedding:
            return []
        matches = self.embedding_index.search(entity.embedding, top_k=top_k + 1)
        results: list[SearchResult] = []
        for mid, score in matches:
            if mid == file_id:
                continue
            me = self.store.get_file(mid)
            if me:
                results.append(SearchResult(file=me, score=score, match_type="similarity"))
        return results[:top_k]

    def get_related(self, file_id: str) -> list[FileEntity]:
        return self.store.get_related(file_id)

    def get_dependencies(self, file_id: str) -> list[FileEntity]:
        return self.store.get_dependencies(file_id)

    def suggest_organization(self, path: Optional[Path] = None) -> OrganizationSuggestion:
        target = path or self.config.root_path
        files = list(target.rglob("*"))
        file_entities = [f for f in files if f.is_file() and not f.name.startswith('.')]
        folders = [f for f in files if f.is_dir() and not f.name.startswith('.')]

        categories: dict[str, list[str]] = {
            "src/": [], "tests/": [], "docs/": [], "config/": [], "assets/": []
        }
        for fp in file_entities:
            ext = fp.suffix.lower()
            name = fp.name.lower()
            if ext in (".py", ".js", ".ts", ".c", ".h", ".cpp", ".rs", ".go", ".java"):
                categories["src/"].append(str(fp))
            elif "test" in name or "spec" in name:
                categories["tests/"].append(str(fp))
            elif ext in (".md", ".txt", ".rst"):
                categories["docs/"].append(str(fp))
            elif ext in (".toml", ".yaml", ".json", ".cfg", ".ini"):
                categories["config/"].append(str(fp))
            else:
                categories["assets/"].append(str(fp))

        non_empty = {k: v for k, v in categories.items() if v}
        scored = sum(len(v) for v in non_empty.values()) / max(len(file_entities), 1)

        return OrganizationSuggestion(
            current_files=len(file_entities),
            current_folders=len(folders),
            suggested_structure=non_empty,
            confidence=scored,
            rationale=f"Found {len(non_empty)} categories covering {scored:.0%} of files",
        )

    def dependency_graph(self, file_id: str, depth: int = 3) -> dict[str, Any]:
        visited: set[str] = set()
        graph: dict[str, list[str]] = {}

        def _traverse(fid: str, d: int):
            if fid in visited or d == 0:
                return
            visited.add(fid)
            deps = self.store.get_dependencies(fid)
            graph[fid] = [d.id for d in deps]
            for dep in deps:
                _traverse(dep.id, d - 1)

        _traverse(file_id, depth)
        return {"root": file_id, "graph": graph}

    def impact_analysis(self, file_id: str) -> dict[str, Any]:
        affected = set()
        queue = [file_id]
        while queue:
            current = queue.pop(0)
            if current in affected:
                continue
            affected.add(current)
            related = self.store.get_related(current)
            for r in related:
                if r.id not in affected:
                    queue.append(r.id)
        return {"file": file_id, "affected_count": len(affected), "affected_ids": list(affected)}

    def get_stats(self) -> dict[str, Any]:
        store_stats = self.store.get_stats()
        return {
            "files_indexed": store_stats["files"],
            "relationships": store_stats["relationships"],
            "embedding_dim": self.config.embedding_dim,
            "model": self.config.embedding_model if self._embedding_model else None,
        }

    def close(self):
        self.store.close()
