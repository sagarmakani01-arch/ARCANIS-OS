from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MemoryConfig:
    """Configuration for the ArcanisMemory engine.

    Mirrors the conventions used by ``arcanis_brain.config.BrainConfig`` so the
    two systems can be wired together with shared storage settings.
    """

    storage_path: str = "arcanis_memory.db"
    storage_backend: str = "arcanisdb"
    encryption_key: Optional[str] = None
    embedding_dim: int = 1536
    embedding_model: str = "text-embedding-3-small"

    default_ttl_seconds: dict[str, int] = field(default_factory=lambda: {
        "SHORT_TERM": 3600,
        "EVENT": 31536000,
    })

    # Forgetting policy
    auto_forget_expired: bool = True
    auto_forget_below_importance: float = 0.0
    max_memories_per_scope: int = 100000

    # Ranking weights (must sum to ~1.0 when normalized)
    weight_importance: float = 0.5
    weight_recency: float = 0.3
    weight_access: float = 0.2

    enable_summarization: bool = True
    enable_relationship_detection: bool = True
    enable_encryption: bool = True

    log_level: str = "INFO"
