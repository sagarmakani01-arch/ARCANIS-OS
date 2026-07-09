"""ArcanisShell — runtime configuration.

Loads defaults and (optionally) a TOML config file. No hardcoded secrets;
paths default to the current working directory and a local log file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ShellConfig:
    """Runtime configuration for the shell."""

    sandbox_root: Path = field(default_factory=Path.cwd)
    history_file: Path = field(default_factory=lambda: Path.home() / ".arcanis_shell_history")
    log_file: Optional[Path] = field(
        default_factory=lambda: Path.home() / ".arcanis_shell_activity.log"
    )
    ai_backend: str = "arcanis_brain"
    prompt: str = "arcanis ❯"
    auto_approve_ai: bool = False
    allow_sandbox_writes: bool = True
    enable_network: bool = False

    @classmethod
    def default(cls) -> "ShellConfig":
        return cls()

    @classmethod
    def from_file(cls, path: Path) -> "ShellConfig":
        import tomllib  # type: ignore

        data = tomllib.loads(path.read_text(encoding="utf-8"))
        cfg = cls.default()
        if "sandbox_root" in data:
            cfg.sandbox_root = Path(data["sandbox_root"]).expanduser()
        if "log_file" in data and data["log_file"]:
            cfg.log_file = Path(data["log_file"]).expanduser()
        cfg.ai_backend = data.get("ai_backend", cfg.ai_backend)
        cfg.prompt = data.get("prompt", cfg.prompt)
        cfg.auto_approve_ai = data.get("auto_approve_ai", cfg.auto_approve_ai)
        cfg.allow_sandbox_writes = data.get("allow_sandbox_writes", cfg.allow_sandbox_writes)
        cfg.enable_network = data.get("enable_network", cfg.enable_network)
        return cfg
