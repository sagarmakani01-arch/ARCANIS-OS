"""Permission system — capability-based access control."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Iterable


class Permission(enum.Enum):
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    AGENT_DELEGATE = "agent:delegate"
    AGENT_SPAWN = "agent:spawn"
    OS_EXECUTE = "os:execute"
    OS_READ = "os:read"
    NETWORK_FETCH = "network:fetch"
    SECURITY_SCAN = "security:scan"
    CODE_WRITE = "code:write"
    CODE_REVIEW = "code:review"


class Role(enum.Enum):
    DEVELOPER = "developer"
    RESEARCHER = "researcher"
    AUTOMATOR = "automator"
    SECURITY = "security"
    SYSTEM = "system"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.DEVELOPER: {
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
        Permission.CODE_WRITE, Permission.CODE_REVIEW, Permission.AGENT_DELEGATE,
    },
    Role.RESEARCHER: {
        Permission.MEMORY_READ, Permission.MEMORY_WRITE, Permission.NETWORK_FETCH,
    },
    Role.AUTOMATOR: {
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
        Permission.OS_EXECUTE, Permission.OS_READ, Permission.AGENT_DELEGATE,
    },
    Role.SECURITY: {
        Permission.MEMORY_READ, Permission.SECURITY_SCAN,
        Permission.OS_READ, Permission.CODE_REVIEW, Permission.AGENT_DELEGATE,
    },
    Role.SYSTEM: {
        Permission.MEMORY_READ, Permission.MEMORY_WRITE,
        Permission.OS_EXECUTE, Permission.OS_READ,
        Permission.AGENT_DELEGATE, Permission.AGENT_SPAWN,
    },
    Role.ADMIN: set(Permission),
}


@dataclass
class AgentIdentity:
    agent_id: str
    name: str
    roles: set[Role] = field(default_factory=set)
    extra: set[Permission] = field(default_factory=set)

    def permissions(self) -> set[Permission]:
        perms = set(self.extra)
        for role in self.roles:
            perms |= ROLE_PERMISSIONS.get(role, set())
        return perms


class PermissionSystem:
    def __init__(self) -> None:
        self._identities: dict[str, AgentIdentity] = {}

    def register(self, identity: AgentIdentity) -> None:
        self._identities[identity.agent_id] = identity

    def register_agent(self, agent_id: str, name: str, roles: Iterable[Role]) -> AgentIdentity:
        ident = AgentIdentity(agent_id=agent_id, name=name, roles=set(roles))
        self.register(ident)
        return ident

    def grant(self, agent_id: str, perm: Permission) -> None:
        ident = self._identities.get(agent_id)
        if ident:
            ident.extra.add(perm)

    def revoke(self, agent_id: str, perm: Permission) -> None:
        ident = self._identities.get(agent_id)
        if ident:
            ident.extra.discard(perm)

    def check(self, agent_id: str, perm: Permission) -> bool:
        ident = self._identities.get(agent_id)
        if not ident:
            return False
        return perm in ident.permissions()

    def require(self, agent_id: str, perm: Permission) -> None:
        if not self.check(agent_id, perm):
            raise PermissionError(f"Agent {agent_id} lacks permission {perm.value}")

    def roles_of(self, agent_id: str) -> set[Role]:
        ident = self._identities.get(agent_id)
        return ident.roles if ident else set()

    def list_agents(self) -> list[AgentIdentity]:
        return list(self._identities.values())
