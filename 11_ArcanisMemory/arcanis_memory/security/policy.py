"""Security layer: user control, memory permissions, and data encryption.

The security layer enforces *who* may read, write, or forget memories in a
given scope, and provides helpers to encrypt/decrypt memory content at rest
using ArcanisDatabase's :class:`CryptoEngine`.
"""

from __future__ import annotations

from typing import Optional

from arcanis_memory.core.types import (
    MemoryScope,
    Permission,
    PermissionLevel,
)


class MemorySecurity:
    """Policy and encryption helpers for the memory engine."""

    def __init__(self, crypto=None, default_level: PermissionLevel = PermissionLevel.WRITE):
        self._crypto = crypto
        self._grants: dict[tuple[str, str], Permission] = {}
        self._default_level = default_level

    # --- Permissions -----------------------------------------------------------

    def grant(self, principal_id: str, resource: str, level: PermissionLevel) -> Permission:
        perm = Permission(resource=resource, level=level, principal_id=principal_id, granted=True)
        self._grants[(principal_id, resource)] = perm
        return perm

    def revoke(self, principal_id: str, resource: str) -> None:
        self._grants.pop((principal_id, resource), None)

    def _resource_for(self, scope: MemoryScope, user_id: str) -> str:
        if scope == MemoryScope.GLOBAL:
            return "global"
        if scope == MemoryScope.PROJECT:
            return f"project:{user_id}"
        if scope == MemoryScope.SESSION:
            return f"session:{user_id}"
        return f"user:{user_id}"

    def check(
        self,
        principal_id: str,
        scope: MemoryScope,
        user_id: str,
        required: PermissionLevel,
    ) -> bool:
        resource = self._resource_for(scope, user_id)
        explicit = self._grants.get((principal_id, resource))
        if explicit is not None:
            return explicit.allows(required)
        # Owners may act on their own scope by default up to the configured level.
        if principal_id == user_id:
            return self._default_level.implies(required)
        return self._default_level.implies(required) and scope != MemoryScope.GLOBAL

    def can_read(self, principal_id: str, scope: MemoryScope, user_id: str) -> bool:
        return self.check(principal_id, scope, user_id, PermissionLevel.READ)

    def can_write(self, principal_id: str, scope: MemoryScope, user_id: str) -> bool:
        return self.check(principal_id, scope, user_id, PermissionLevel.WRITE)

    def can_forget(self, principal_id: str, scope: MemoryScope, user_id: str) -> bool:
        return self.check(principal_id, scope, user_id, PermissionLevel.FORGET)

    # --- Encryption ------------------------------------------------------------

    def is_encrypted(self) -> bool:
        return self._crypto is not None

    def encrypt_content(self, content: str) -> tuple[str, bool]:
        if self._crypto is None:
            return content, False
        return self._crypto.encrypt(content), True

    def decrypt_content(self, content: str, was_encrypted: bool) -> str:
        if not was_encrypted or self._crypto is None:
            return content
        return self._crypto.decrypt(content)

    def list_grants(self) -> list[Permission]:
        return list(self._grants.values())
