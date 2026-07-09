from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Capability(Enum):
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    FILE_DELETE = "file:delete"
    FILE_EXECUTE = "file:execute"
    PROCESS_CREATE = "process:create"
    PROCESS_KILL = "process:kill"
    NET_CONNECT = "net:connect"
    NET_LISTEN = "net:listen"
    SYS_SHUTDOWN = "sys:shutdown"
    SYS_REBOOT = "sys:reboot"
    AI_INFER = "ai:infer"
    AI_TRAIN = "ai:train"
    CAPABILITY_GRANT = "capability:grant"
    CAPABILITY_REVOKE = "capability:revoke"
    ALL = "*"


class CapabilityScope(Enum):
    PROCESS = "process"
    USER = "user"
    SYSTEM = "system"
    TEMPORARY = "temporary"


@dataclass
class CapabilityToken:
    token_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    capability: Capability = Capability.ALL
    scope: CapabilityScope = CapabilityScope.PROCESS
    subject_id: str = ""
    resource_pattern: str = "*"
    granted_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    max_uses: Optional[int] = None
    use_count: int = 0
    constraints: dict[str, Any] = field(default_factory=dict)
    parent_token_id: Optional[str] = None
    revoked: bool = False

    def is_valid(self) -> bool:
        if self.revoked:
            return False
        if self.expires_at and time.time() > self.expires_at:
            return False
        if self.max_uses and self.use_count >= self.max_uses:
            return False
        return True

    def consume(self) -> bool:
        if not self.is_valid():
            return False
        self.use_count += 1
        return True

    def matches_resource(self, resource: str) -> bool:
        if self.resource_pattern == "*":
            return True
        if self.resource_pattern in resource:
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "capability": self.capability.value,
            "scope": self.scope.value,
            "subject_id": self.subject_id,
            "resource_pattern": self.resource_pattern,
            "granted_at": self.granted_at,
            "expires_at": self.expires_at,
            "max_uses": self.max_uses,
            "use_count": self.use_count,
            "constraints": self.constraints,
            "parent_token_id": self.parent_token_id,
            "revoked": self.revoked,
        }

    def signature(self) -> str:
        data = json.dumps({
            "token_id": self.token_id,
            "capability": self.capability.value,
            "subject_id": self.subject_id,
            "resource_pattern": self.resource_pattern,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def delegate(self, capability: Capability, resource: str,
                 expires_in: Optional[float] = None,
                 max_uses: Optional[int] = None) -> CapabilityToken:
        if self.capability != Capability.ALL and self.capability != capability:
            raise ValueError(f"Cannot delegate {capability.value} with {self.capability.value}")
        return CapabilityToken(
            capability=capability,
            scope=CapabilityScope.TEMPORARY,
            subject_id=self.subject_id,
            resource_pattern=resource,
            expires_at=time.time() + expires_in if expires_in else None,
            max_uses=max_uses,
            parent_token_id=self.token_id,
            constraints={**self.constraints, "delegated": True},
        )
