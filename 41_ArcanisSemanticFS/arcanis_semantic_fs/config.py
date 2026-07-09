from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SemanticFSConfig:
    root_path: Path = field(default_factory=Path.cwd)
    db_path: Optional[Path] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    max_file_size_mb: int = 100
    auto_index: bool = True
    index_on_save: bool = True
    cache_embeddings: bool = True
    similarity_threshold: float = 0.7
    max_search_results: int = 20

    def __post_init__(self):
        if self.db_path is None:
            self.db_path = self.root_path / ".arcanis" / "semantic.db"
