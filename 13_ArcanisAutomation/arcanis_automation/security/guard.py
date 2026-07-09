"""Security: permission control, safe execution sandbox, and audit logging."""

from __future__ import annotations

import json
import logging
import os
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional

from arcanis_automation.core.models import Permission, PermissionLevel


class SecurityError(Exception):
    """Raised when an action is denied by the security layer."""


class AuditLogger:
    """Append-only audit log of every execution attempt and decision."""

    def __init__(self, log_dir: str, enabled: bool = True):
        self.log_dir = log_dir
        self.enabled = enabled
        self._logger = logging.getLogger("arcanis_automation.audit")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False
        if enabled:
            os.makedirs(log_dir, exist_ok=True)
            path = os.path.join(log_dir, "audit.log")
            if not any(isinstance(h, logging.FileHandler) for h in self._logger.handlers):
                handler = logging.FileHandler(path, encoding="utf-8")
                handler.setFormatter(
                    logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
                )
                self._logger.addHandler(handler)

    def record(self, event: str, **fields: Any) -> None:
        if not self.enabled:
            return
        payload = " ".join(f"{k}={v}" for k, v in fields.items())
        self._logger.info(f"{event} {payload}")

    def read(self, limit: int = 200) -> list[str]:
        path = os.path.join(self.log_dir, "audit.log")
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        return lines[-limit:]


@dataclass
class SecurityContext:
    """Decides whether actions may run and how they execute."""

    permissions: list[Permission] = None  # type: ignore
    safe_mode: bool = True
    allowed_paths: list[str] | None = None

    def __post_init__(self) -> None:
        self.permissions = self.permissions or [
            Permission(PermissionLevel.EXECUTE, "*")
        ]

    def check(self, action: str) -> bool:
        # Deny rules win; otherwise any matching grant allows.
        for p in self.permissions:
            if p.level == PermissionLevel.DENY and p.allows(action):
                return False
        for p in self.permissions:
            if p.level in (PermissionLevel.EXECUTE, PermissionLevel.ADMIN) and p.allows(action):
                return True
        return False

    def require(self, action: str) -> None:
        if not self.check(action):
            self.raise_denied(action)

    @staticmethod
    def raise_denied(action: str) -> None:
        raise SecurityError(f"Action '{action}' denied by security policy.")

    def guard_path(self, path: str) -> str:
        """Ensure filesystem operations stay within allowed roots in safe mode."""
        abs_path = os.path.abspath(os.path.expanduser(path))
        if not self.safe_mode:
            return abs_path
        roots = self.allowed_paths or [os.getcwd()]
        if not any(abs_path.startswith(os.path.abspath(r)) for r in roots):
            raise SecurityError(
                f"Path '{path}' is outside allowed roots in safe mode."
            )
        return abs_path

    def run_shell(self, command: str, timeout: float = 30.0) -> subprocess.CompletedProcess:
        """Execute a shell command with restrictions when safe mode is on."""
        self.require("shell")
        if self.safe_mode:
            tokens = shlex.split(command)
            if not tokens:
                raise SecurityError("Empty shell command.")
            # Disallow shell operators that enable chaining/escapes.
            dangerous = {";", "&&", "||", "|", ">", ">>", "<", "&", "$", "`"}
            if any(t in dangerous for t in tokens):
                raise SecurityError(
                    "Dangerous shell operators blocked in safe mode."
                )
            argv = tokens
        else:
            argv = command
        try:
            return subprocess.run(
                argv,
                shell=not self.safe_mode,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise SecurityError(f"Command timed out after {timeout}s.") from exc
