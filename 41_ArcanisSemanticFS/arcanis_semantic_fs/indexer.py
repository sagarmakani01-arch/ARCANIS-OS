from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Optional

from .storage import FileEntity, MetadataStore


CODE_EXTENSIONS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".c": "c", ".h": "c-header", ".cpp": "cpp", ".rs": "rust",
    ".go": "go", ".java": "java", ".rb": "ruby", ".sh": "shell",
    ".arc": "arcanis", ".toml": "config", ".yaml": "config",
    ".json": "config", ".md": "markdown", ".txt": "text",
    ".html": "html", ".css": "css", ".sql": "sql",
}

IMPORT_PATTERNS = {
    "python": [r"^(?:from|import)\s+([\w.]+)", r"^(?:from|import)\s+([\w.]+)\s+import"],
    "javascript": [r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]"],
    "typescript": [r"(?:import|from)\s+['\"]([^'\"]+)['\"]"],
    "c": [r'#include\s+[<"]([^>"]+)[>"]'],
    "cpp": [r'#include\s+[<"]([^>"]+)[>"]'],
    "rust": [r'^(?:extern\s+crate|use)\s+([\w:]+)'],
    "go": [r'^import\s+"([^"]+)"', r'^import\s+\([\s\S]*?"([^"]+)"'],
}


class EmbeddingIndex:
    def __init__(self, dim: int = 384):
        self.dim = dim
        self._vectors: dict[str, list[float]] = {}

    def add(self, file_id: str, embedding: list[float]) -> None:
        self._vectors[file_id] = embedding

    def remove(self, file_id: str) -> None:
        self._vectors.pop(file_id, None)

    def search(self, query_embedding: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        scores: list[tuple[str, float]] = []
        for fid, vec in self._vectors.items():
            sim = self._cosine_similarity(query_embedding, vec)
            scores.append((fid, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if len(a) != len(b) or len(a) == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class ContentAnalyzer:
    def extract_tags(self, content: str, content_type: str) -> list[str]:
        tags: set[str] = set()
        if content_type in ("python", "javascript", "typescript", "c", "cpp", "rust", "go", "java"):
            for match in re.finditer(r'\b(?:class|fun|function|def|fn|func)\s+(\w+)', content):
                tags.add(f"defines:{match.group(1)}")
            for match in re.finditer(r'#include\s+[<"]([^>"]+)', content):
                tags.add(f"includes:{match.group(1)}")
            for match in re.finditer(r'import\s+([\w.]+)', content):
                tags.add(f"imports:{match.group(1).split('.')[0]}")
        elif content_type == "markdown":
            for match in re.finditer(r'^#+\s+(.+)$', content, re.MULTILINE):
                tags.add(f"section:{match.group(1).strip()[:50]}")
        if len(content) > 0:
            lines = content.split('\n')
            tags.add(f"lines:{len(lines)}")
        return sorted(tags)

    def generate_summary(self, content: str, name: str, content_type: str) -> str:
        if not content:
            return f"Empty file: {name}"
        lines = content.strip().split('\n')
        first_line = lines[0].strip() if lines else ""
        if content_type in ("python", "javascript", "typescript", "c", "cpp"):
            classes = re.findall(r'class\s+(\w+)', content)
            functions = re.findall(r'(?:def|function|fn|func)\s+(\w+)', content)
            parts = [f"{name}: {content_type}"]
            if classes:
                parts.append(f"classes: {', '.join(classes[:5])}")
            if functions:
                parts.append(f"functions: {', '.join(functions[:5])}")
            return "; ".join(parts)
        if content_type == "markdown" and first_line.startswith('#'):
            return first_line.lstrip('#').strip()
        return f"{name}: {content_type or 'unknown type'}, {len(lines)} lines"

    def detect_intent(self, content: str, name: str) -> str:
        name_lower = name.lower()
        if "test" in name_lower or "spec" in name_lower:
            return "testing"
        if "config" in name_lower or "settings" in name_lower:
            return "configuration"
        if "readme" in name_lower or "doc" in name_lower:
            return "documentation"
        if "main" in name_lower or "app" in name_lower or "index" in name_lower:
            return "entry_point"
        if re.search(r'class\s+\w+', content):
            return "module_definition"
        return "implementation"

    def extract_imports(self, content: str, content_type: str) -> list[str]:
        patterns = IMPORT_PATTERNS.get(content_type, [])
        imports: list[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(1))
        return imports


class SemanticIndexer:
    def __init__(self, store: MetadataStore, embedding_index: EmbeddingIndex):
        self.store = store
        self.embedding_index = embedding_index
        self.analyzer = ContentAnalyzer()

    def index_file(self, file_path: Path, embedding_model=None) -> Optional[FileEntity]:
        if not file_path.exists() or not file_path.is_file():
            return None

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = ""

        ext = file_path.suffix.lower()
        content_type = CODE_EXTENSIONS.get(ext, "unknown")

        entity = FileEntity(
            path=str(file_path),
            name=file_path.name,
            content_type=content_type,
            size=file_path.stat().st_size,
        )

        entity.tags = self.analyzer.extract_tags(content, content_type)
        entity.summary = self.analyzer.generate_summary(content, entity.name, content_type)
        entity.intent = self.analyzer.detect_intent(content, entity.name)

        if embedding_model and content:
            try:
                entity.embedding = embedding_model.encode(content[:8192]).tolist()
            except Exception:
                entity.embedding = None

        self.store.upsert_file(entity)

        if entity.embedding:
            self.embedding_index.add(entity.id, entity.embedding)

        imports = self.analyzer.extract_imports(content, content_type)
        for imp in imports:
            related = self.store.search_files(imp.split('.')[0], limit=3)
            for rel in related:
                if rel.id != entity.id:
                    from .storage import Relationship
                    self.store.add_relationship(Relationship(
                        source_id=entity.id, target_id=rel.id,
                        rel_type="depends_on", confidence=0.8
                    ))

        return entity

    def index_directory(self, directory: Path, embedding_model=None) -> list[FileEntity]:
        indexed: list[FileEntity] = []
        for file_path in directory.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                entity = self.index_file(file_path, embedding_model)
                if entity:
                    indexed.append(entity)
        return indexed
