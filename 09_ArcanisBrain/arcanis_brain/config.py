from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BrainConfig:
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    memory_ttl_seconds: int = 3600
    max_long_term_memories: int = 10000
    enable_audit: bool = True
    safety_mode: str = "strict"
    agent_timeout_seconds: int = 300
    personality_profile: str = "default"
    storage_backend: str = "json"
    storage_path: str = "~/.arcanis/brain"
    log_level: str = "INFO"
    allowed_tools: list[str] = field(default_factory=lambda: ["read", "write", "search", "execute"])
    max_concurrent_agents: int = 10
    embedding_model: str = "text-embedding-3-small"
    context_window: int = 128000
