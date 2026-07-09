"""Capability security integration — bridges 50_ArcanisSecurity with the rest of the ecosystem."""

from __future__ import annotations

import time
from typing import Any, Optional

from ..capability import Capability, CapabilityToken, CapabilityScope
from ..manager import CapabilityManager, SecurityPolicy


class SystemPolicy:
    """Default security policy for the Arcanis OS.

    Defines which capabilities are granted by default to different process types,
    and which operations always require explicit authorization.
    """

    def __init__(self):
        self._process_policies: dict[str, dict[str, Any]] = {
            "shell": {
                "default_capabilities": [Capability.FILE_READ, Capability.FILE_WRITE, Capability.PROCESS_CREATE],
                "denied": [Capability.SYS_SHUTDOWN, Capability.SYS_REBOOT],
                "max_file_ops_per_second": 50,
            },
            "driver": {
                "default_capabilities": [Capability.NET_CONNECT, Capability.FILE_READ],
                "denied": [Capability.CAPABILITY_GRANT, Capability.AI_TRAIN],
                "max_file_ops_per_second": 100,
            },
            "inference": {
                "default_capabilities": [Capability.AI_INFER, Capability.FILE_READ],
                "denied": [Capability.FILE_WRITE, Capability.PROCESS_CREATE],
                "max_file_ops_per_second": 10,
            },
            "admin": {
                "default_capabilities": list(Capability),
                "denied": [],
                "max_file_ops_per_second": 200,
            },
        }

    def get_capabilities_for_role(self, role: str) -> list[Capability]:
        policy = self._process_policies.get(role, self._process_policies["shell"])
        return list(policy["default_capabilities"])

    def get_denied_for_role(self, role: str) -> list[Capability]:
        policy = self._process_policies.get(role, self._process_policies["shell"])
        return list(policy["denied"])


class CapabilityIntegrator:
    """Integrates capability-based security across the Arcanis ecosystem.

    Provides a unified interface for:
    - Shell: check permissions before command execution
    - Kernel: validate syscall capabilities
    - Brain: authorize inference requests
    - FS: control file access
    """

    def __init__(self, manager: Optional[CapabilityManager] = None):
        self.manager = manager or CapabilityManager()
        self.system_policy = SystemPolicy()
        self._process_tokens: dict[int, list[str]] = {}

    def initialize(self) -> None:
        self.manager.grant(
            Capability.ALL, "system", "*",
            constraints={"role": "admin", "source": "system_init"},
        )

    def spawn_process(self, pid: int, role: str, name: str = "") -> list[CapabilityToken]:
        caps = self.system_policy.get_capabilities_for_role(role)
        denied = self.system_policy.get_denied_for_role(role)
        granted_caps = [c for c in caps if c not in denied]

        tokens: list[CapabilityToken] = []
        self._process_tokens[pid] = []
        for cap in granted_caps:
            token = self.manager.grant(cap, f"process-{pid}", constraints={"role": role, "name": name})
            tokens.append(token)
            self._process_tokens[pid].append(token.token_id)
        return tokens

    def check_permission(self, pid: int, capability: Capability, resource: str = "*") -> bool:
        token_ids = self._process_tokens.get(pid, [])
        for tid in token_ids:
            token = self.manager._tokens.get(tid)
            if token and token.is_valid() and token.capability == capability:
                return self.manager.authorize(tid, capability.value, resource)
        return False

    def terminate_process(self, pid: int) -> int:
        token_ids = self._process_tokens.pop(pid, [])
        revoked = 0
        for tid in token_ids:
            if self.manager.revoke(tid):
                revoked += 1
        return revoked

    def get_process_capabilities(self, pid: int) -> list[dict[str, Any]]:
        token_ids = self._process_tokens.get(pid, [])
        caps = []
        for tid in token_ids:
            token = self.manager._tokens.get(tid)
            if token:
                caps.append({
                    "capability": token.capability.value,
                    "valid": token.is_valid(),
                    "resource": token.resource_pattern,
                })
        return caps

    def get_audit_summary(self) -> dict:
        return self.manager.audit.stats()
