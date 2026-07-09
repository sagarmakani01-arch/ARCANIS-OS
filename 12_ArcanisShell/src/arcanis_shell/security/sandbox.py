"""ArcanisShell — sandbox boundary enforcement.

Limits filesystem operations to an allowed root directory and blocks
network / process-spawning actions unless explicitly enabled. The sandbox
is a guardrail for AI-generated and automation actions; traditional user
commands can opt out via a policy but still respect the deny set.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..errors import SandboxViolationError
from ..types import CommandSource, RiskLevel


class Sandbox:
    """Filesystem and capability boundary for untrusted actions."""

    def __init__(
        self,
        root: Path,
        allow_network: bool = False,
        allow_subprocess: bool = True,
        allow_write: bool = True,
    ) -> None:
        self.root = root.resolve()
        self.allow_network = allow_network
        self.allow_subprocess = allow_subprocess
        self.allow_write = allow_write

    def is_inside(self, path: Path) -> bool:
        resolved = Path(path).resolve()
        return resolved == self.root or self.root in resolved.parents

    def require_inside(self, path: Path) -> Path:
        if not self.is_inside(path):
            raise SandboxViolationError("filesystem access outside sandbox", path)
        return Path(path).resolve()

    def guard_write(self) -> None:
        if not self.allow_write:
            raise SandboxViolationError("write operation disabled by sandbox")

    def guard_network(self) -> None:
        if not self.allow_network:
            raise SandboxViolationError("network access disabled by sandbox")

    def guard_subprocess(self, source: CommandSource, risk: RiskLevel) -> None:
        if not self.allow_subprocess and source != CommandSource.TRADITIONAL:
            raise SandboxViolationError("subprocess spawn disabled by sandbox")

    def allowed_paths(self) -> Iterable[Path]:
        return [self.root]
