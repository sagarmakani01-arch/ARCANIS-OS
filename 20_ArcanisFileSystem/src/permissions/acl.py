"""Access Control List (ACL) system for ArcanisFileSystem.

Provides fine-grained permission control beyond standard POSIX permissions.
"""

import enum
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ACLPermission(enum.IntFlag):
    """ACL permission bits."""
    NONE = 0
    READ = 1 << 0
    WRITE = 1 << 1
    EXECUTE = 1 << 2
    DELETE = 1 << 3
    ADMIN = 1 << 4
    FULL_CONTROL = READ | WRITE | EXECUTE | DELETE | ADMIN


class ACLScope(enum.Enum):
    """Scope of ACL entry."""
    USER = "user"
    GROUP = "group"
    OTHER = "other"
    NAMED_USER = "named_user"
    NAMED_GROUP = "named_group"
    OWNER = "owner"
    EVERYONE = "everyone"


@dataclass
class ACLEntry:
    """Single ACL entry mapping an identity to permissions."""

    scope: ACLScope
    identity: Optional[str] = None
    permissions: ACLPermission = ACLPermission.NONE
    inherit: bool = False

    def allows(self, perm: ACLPermission) -> bool:
        return bool(self.permissions & perm)

    def grant(self, perm: ACLPermission) -> None:
        self.permissions |= perm

    def revoke(self, perm: ACLPermission) -> None:
        self.permissions &= ~perm

    def to_dict(self) -> dict:
        return {
            "scope": self.scope.value,
            "identity": self.identity,
            "permissions": int(self.permissions),
            "inherit": self.inherit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ACLEntry":
        return cls(
            scope=ACLScope(data["scope"]),
            identity=data.get("identity"),
            permissions=ACLPermission(data["permissions"]),
            inherit=data.get("inherit", False),
        )


@dataclass
class ACL:
    """Access Control List for a file or directory."""

    id: uuid.UUID = field(default_factory=uuid.uuid4)
    entries: List[ACLEntry] = field(default_factory=list)
    default_entries: List[ACLEntry] = field(default_factory=list)

    def add_entry(self, entry: ACLEntry) -> None:
        for existing in self.entries:
            if existing.scope == entry.scope and existing.identity == entry.identity:
                existing.permissions = entry.permissions
                return
        self.entries.append(entry)

    def remove_entry(self, scope: ACLScope, identity: Optional[str] = None) -> bool:
        for i, entry in enumerate(self.entries):
            if entry.scope == scope and entry.identity == identity:
                self.entries.pop(i)
                return True
        return False

    def get_entry(self, scope: ACLScope, identity: Optional[str] = None) -> Optional[ACLEntry]:
        for entry in self.entries:
            if entry.scope == scope and entry.identity == identity:
                return entry
        return None

    def check_permission(self, uid: int, gid: int, user_groups: List[int], perm: ACLPermission, file_uid: int, file_gid: int) -> bool:
        if uid == file_uid:
            owner_entry = self.get_entry(ACLScope.OWNER)
            if owner_entry and owner_entry.allows(perm):
                return True

        everyone_entry = self.get_entry(ACLScope.EVERYONE)
        if everyone_entry and everyone_entry.allows(perm):
            return True

        for entry in self.entries:
            if entry.scope == ACLScope.NAMED_USER and entry.identity == str(uid):
                if entry.allows(perm):
                    return True

            elif entry.scope == ACLScope.NAMED_GROUP and entry.identity:
                try:
                    group_id = int(entry.identity)
                    if group_id in user_groups and entry.allows(perm):
                        return True
                except ValueError:
                    pass

            elif entry.scope == ACLScope.GROUP and gid == file_gid:
                if entry.allows(perm):
                    return True

            elif entry.scope == ACLScope.OTHER:
                if entry.allows(perm):
                    return True

        return False

    def inherit_defaults(self) -> None:
        for default in self.default_entries:
            existing = self.get_entry(default.scope, default.identity)
            if not existing:
                new_entry = ACLEntry(
                    scope=default.scope,
                    identity=default.identity,
                    permissions=default.permissions,
                    inherit=True,
                )
                self.entries.append(new_entry)

    def set_default(self, entry: ACLEntry) -> None:
        entry.inherit = True
        for i, existing in enumerate(self.default_entries):
            if existing.scope == entry.scope and existing.identity == entry.identity:
                self.default_entries[i] = entry
                return
        self.default_entries.append(entry)

    def remove_default(self, scope: ACLScope, identity: Optional[str] = None) -> bool:
        for i, entry in enumerate(self.default_entries):
            if entry.scope == scope and entry.identity == identity:
                self.default_entries.pop(i)
                return True
        return False

    def count(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "entries": [e.to_dict() for e in self.entries],
            "defaults": [e.to_dict() for e in self.default_entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ACL":
        acl = cls(id=uuid.UUID(data["id"]))
        acl.entries = [ACLEntry.from_dict(e) for e in data.get("entries", [])]
        acl.default_entries = [ACLEntry.from_dict(e) for e in data.get("defaults", [])]
        return acl
