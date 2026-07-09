"""Configuration for the automation engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutomationConfig:
    """Engine-wide configuration."""

    workspace_dir: str = field(
        default_factory=lambda: os.path.join(os.getcwd(), "automation_workspace")
    )
    storage_dir: str = field(
        default_factory=lambda: os.path.join(os.getcwd(), "automation_store")
    )
    log_dir: str = field(
        default_factory=lambda: os.path.join(os.getcwd(), "automation_logs")
    )
    enable_scheduler: bool = True
    default_permission_level: str = "execute"
    safe_mode: bool = True
    max_concurrent_steps: int = 8
    audit_all: bool = True
    ai_provider: str = "local"
    metadata: dict[str, Any] = field(default_factory=dict)

    def ensure_dirs(self) -> None:
        for d in (self.workspace_dir, self.storage_dir, self.log_dir):
            os.makedirs(d, exist_ok=True)
