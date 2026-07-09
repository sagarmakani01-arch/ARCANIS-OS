"""Audit logging system for ArcanisFileSystem.

Tracks all filesystem operations for security and compliance.
"""

import json
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent(Enum):
    FILE_CREATE = "file.create"
    FILE_DELETE = "file.delete"
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_RENAME = "file.rename"
    FILE_MOVE = "file.move"
    FILE_COPY = "file.copy"
    FILE_CHMOD = "file.chmod"
    FILE_ENCRYPT = "file.encrypt"
    FILE_DECRYPT = "file.decrypt"
    DIR_CREATE = "dir.create"
    DIR_DELETE = "dir.delete"
    DIR_LIST = "dir.list"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATE = "user.create"
    USER_DELETE = "user.delete"
    PERMISSION_DENIED = "permission.denied"
    SNAPSHOT_CREATE = "snapshot.create"
    SNAPSHOT_RESTORE = "snapshot.restore"
    SYSTEM_ERROR = "system.error"


@dataclass
class AuditEntry:
    """Single audit log entry."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    event: AuditEvent = AuditEvent.SYSTEM_ERROR
    level: AuditLevel = AuditLevel.INFO
    user_id: Optional[int] = None
    username: Optional[str] = None
    path: Optional[str] = None
    details: Dict = field(default_factory=dict)
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "event": self.event.value,
            "level": self.level.value,
            "user_id": self.user_id,
            "username": self.username,
            "path": self.path,
            "details": self.details,
            "ip_address": self.ip_address,
            "session_id": self.session_id,
            "success": self.success,
            "error": self.error_message,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class AuditLogger:
    """Manages audit logging for the filesystem."""

    MAX_ENTRIES = 1000000
    FLUSH_INTERVAL = 60

    def __init__(self, max_entries: int = MAX_ENTRIES):
        self.max_entries = max_entries
        self._entries: List[AuditEntry] = []
        self._callbacks: List[Callable[[AuditEntry], None]] = []
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._last_flush = time.time()

    def log(self, event: AuditEvent, level: AuditLevel = AuditLevel.INFO, user_id: Optional[int] = None, username: Optional[str] = None, path: Optional[str] = None, details: Optional[Dict] = None, ip_address: Optional[str] = None, session_id: Optional[str] = None, success: bool = True, error_message: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(
            event=event,
            level=level,
            user_id=user_id,
            username=username,
            path=path,
            details=details or {},
            ip_address=ip_address,
            session_id=session_id,
            success=success,
            error_message=error_message,
        )

        self._entries.append(entry)
        self._event_counts[event.value] += 1

        for callback in self._callbacks:
            try:
                callback(entry)
            except Exception:
                pass

        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries // 2:]

        return entry

    def log_file_operation(self, event: AuditEvent, path: str, user_id: int, username: str, success: bool = True, details: Optional[Dict] = None, error: Optional[str] = None) -> AuditEntry:
        return self.log(
            event=event,
            user_id=user_id,
            username=username,
            path=path,
            details=details or {},
            success=success,
            error_message=error,
        )

    def log_permission_denied(self, path: str, user_id: int, username: str, operation: str) -> AuditEntry:
        return self.log(
            event=AuditEvent.PERMISSION_DENIED,
            level=AuditLevel.WARNING,
            user_id=user_id,
            username=username,
            path=path,
            details={"operation": operation},
            success=False,
        )

    def log_security_event(self, event: AuditEvent, details: Dict, user_id: Optional[int] = None, ip_address: Optional[str] = None) -> AuditEntry:
        return self.log(
            event=event,
            level=AuditLevel.CRITICAL,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
        )

    def add_callback(self, callback: Callable[[AuditEntry], None]) -> None:
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[AuditEntry], None]) -> bool:
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            return True
        return False

    def query(self, event: Optional[AuditEvent] = None, level: Optional[AuditLevel] = None, user_id: Optional[int] = None, path: Optional[str] = None, start_time: Optional[float] = None, end_time: Optional[float] = None, limit: int = 1000) -> List[AuditEntry]:
        results = []

        for entry in reversed(self._entries):
            if len(results) >= limit:
                break

            if event and entry.event != event:
                continue
            if level and entry.level != level:
                continue
            if user_id is not None and entry.user_id != user_id:
                continue
            if path and entry.path != path:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue

            results.append(entry)

        return results

    def get_event_statistics(self) -> Dict[str, int]:
        return dict(self._event_counts)

    def get_user_activity(self, user_id: int) -> List[AuditEntry]:
        return [e for e in self._entries if e.user_id == user_id]

    def get_path_activity(self, path: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.path == path]

    def get_recent_entries(self, count: int = 100) -> List[AuditEntry]:
        return list(reversed(self._entries[-count:]))

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        self._event_counts.clear()
        return count

    def export_json(self, filepath: str) -> int:
        with open(filepath, "w") as f:
            json.dump([e.to_dict() for e in self._entries], f, indent=2)
        return len(self._entries)

    def get_info(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "max_entries": self.max_entries,
            "callbacks": len(self._callbacks),
            "event_counts": dict(self._event_counts),
        }
