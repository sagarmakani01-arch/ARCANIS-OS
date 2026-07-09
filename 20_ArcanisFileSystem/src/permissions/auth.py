"""Authentication system for ArcanisFileSystem.

Manages users, sessions, and authentication for filesystem access.
"""

import hashlib
import secrets
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class User:
    """Represents a filesystem user."""

    id: int
    username: str
    primary_group: int
    groups: List[int] = field(default_factory=list)
    home_directory: str = ""
    shell: str = "/bin/sh"
    is_active: bool = True
    password_hash: Optional[str] = None
    salt: Optional[str] = None

    def set_password(self, password: str) -> None:
        self.salt = secrets.token_hex(32)
        self.password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), self.salt.encode(), 100000
        ).hex()

    def verify_password(self, password: str) -> bool:
        if not self.password_hash or not self.salt:
            return False
        test_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), self.salt.encode(), 100000
        ).hex()
        return secrets.compare_digest(self.password_hash, test_hash)

    def is_in_group(self, gid: int) -> bool:
        return gid == self.primary_group or gid in self.groups

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "primary_group": self.primary_group,
            "groups": self.groups,
            "home": self.home_directory,
            "shell": self.shell,
            "active": self.is_active,
        }


@dataclass
class Session:
    """Represents an authenticated session."""

    id: str = field(default_factory=lambda: secrets.token_hex(32))
    user: User = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    ip_address: Optional[str] = None
    is_valid: bool = True

    def refresh(self) -> None:
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def is_active(self) -> bool:
        return self.is_valid and not self.is_expired()

    def invalidate(self) -> None:
        self.is_valid = False


class Authenticator:
    """Manages user authentication and sessions."""

    ROOT_UID = 0
    NOBODY_UID = 65534

    def __init__(self):
        self._users: Dict[int, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._next_uid = 1000
        self._create_system_users()

    def _create_system_users(self) -> None:
        root = User(
            id=self.ROOT_UID,
            username="root",
            primary_group=0,
            home_directory="/root",
            shell="/bin/bash",
        )
        root.set_password("arcanis_root")
        self._users[self.ROOT_UID] = root

        nobody = User(
            id=self.NOBODY_UID,
            username="nobody",
            primary_group=65534,
            home_directory="/nonexistent",
            shell="/sbin/nologin",
        )
        self._users[self.NOBODY_UID] = nobody

    def create_user(self, username: str, password: str, primary_group: int = 100, home: Optional[str] = None) -> User:
        if self.get_user_by_name(username):
            raise ValueError(f"User '{username}' already exists")

        uid = self._next_uid
        self._next_uid += 1

        user = User(
            id=uid,
            username=username,
            primary_group=primary_group,
            home_directory=home or f"/home/{username}",
        )
        user.set_password(password)
        self._users[uid] = user
        return user

    def get_user(self, uid: int) -> Optional[User]:
        return self._users.get(uid)

    def get_user_by_name(self, username: str) -> Optional[User]:
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def delete_user(self, uid: int) -> bool:
        if uid == self.ROOT_UID:
            raise PermissionError("Cannot delete root user")

        if uid in self._users:
            del self._users[uid]
            return True
        return False

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_name(username)
        if user and user.is_active and user.verify_password(password):
            return user
        return None

    def create_session(self, user: User, timeout: float = 3600, ip_address: Optional[str] = None) -> Session:
        session = Session(
            user=user,
            expires_at=time.time() + timeout,
            ip_address=ip_address,
        )
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session and session.is_active():
            session.refresh()
            return session
        return None

    def invalidate_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.invalidate()
            return True
        return False

    def cleanup_sessions(self) -> int:
        expired = [
            sid for sid, session in self._sessions.items()
            if not session.is_active()
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def list_users(self) -> List[User]:
        return list(self._users.values())

    def is_root(self, uid: int) -> bool:
        return uid == self.ROOT_UID

    def add_to_group(self, uid: int, gid: int) -> bool:
        user = self._users.get(uid)
        if user and gid not in user.groups:
            user.groups.append(gid)
            return True
        return False

    def remove_from_group(self, uid: int, gid: int) -> bool:
        user = self._users.get(uid)
        if user and gid in user.groups:
            user.groups.remove(gid)
            return True
        return False
