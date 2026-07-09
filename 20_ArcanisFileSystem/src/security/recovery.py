"""Recovery system for ArcanisFileSystem.

Provides snapshot-based recovery and filesystem repair capabilities.
"""

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class SnapshotType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class SnapshotStatus(Enum):
    CREATING = "creating"
    COMPLETE = "complete"
    CORRUPTED = "corrupted"
    DELETED = "deleted"


@dataclass
class Snapshot:
    """Represents a filesystem snapshot."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    snapshot_type: SnapshotType = SnapshotType.FULL
    status: SnapshotStatus = SnapshotStatus.CREATING
    created_at: float = field(default_factory=time.time)
    size_bytes: int = 0
    checksum: str = ""
    parent_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    included_inodes: List[str] = field(default_factory=list)

    def complete(self, size: int, checksum: str) -> None:
        self.status = SnapshotStatus.COMPLETE
        self.size_bytes = size
        self.checksum = checksum

    def is_valid(self) -> bool:
        return self.status == SnapshotStatus.COMPLETE

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.snapshot_type.value,
            "status": self.status.value,
            "created": self.created_at,
            "size": self.size_bytes,
            "checksum": self.checksum,
            "parent": self.parent_id,
            "metadata": self.metadata,
        }


@dataclass
class RecoveryPoint:
    """A point in time for recovery."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    snapshot_id: str = ""
    description: str = ""
    is_auto: bool = False


class RecoveryManager:
    """Manages filesystem snapshots and recovery operations."""

    MAX_SNAPSHOTS = 100
    AUTO_SNAPSHOT_INTERVAL = 3600

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._snapshots: Dict[str, Snapshot] = {}
        self._recovery_points: List[RecoveryPoint] = []
        self._last_auto_snapshot = time.time()

    def create_snapshot(self, name: str = "", snapshot_type: SnapshotType = SnapshotType.FULL, parent_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Snapshot:
        if len(self._snapshots) >= self.MAX_SNAPSHOTS:
            self._cleanup_old_snapshots()

        snapshot = Snapshot(
            name=name or f"snapshot_{int(time.time())}",
            snapshot_type=snapshot_type,
            parent_id=parent_id,
            metadata=metadata or {},
        )

        self._snapshots[snapshot.id] = snapshot
        return snapshot

    def complete_snapshot(self, snapshot_id: str, size: int, included_inodes: List[str]) -> Snapshot:
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")

        checksum_data = f"{snapshot_id}:{size}:{len(included_inodes)}".encode()
        checksum = hashlib.sha256(checksum_data).hexdigest()

        snapshot.included_inodes = included_inodes
        snapshot.complete(size, checksum)

        self._add_recovery_point(snapshot_id, f"Snapshot '{snapshot.name}' completed")

        return snapshot

    def delete_snapshot(self, snapshot_id: str) -> bool:
        snapshot = self._snapshots.get(snapshot_id)
        if snapshot:
            snapshot.status = SnapshotStatus.DELETED
            return True
        return False

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(snapshot_id)

    def list_snapshots(self, include_deleted: bool = False) -> List[Snapshot]:
        snapshots = list(self._snapshots.values())
        if not include_deleted:
            snapshots = [s for s in snapshots if s.status != SnapshotStatus.DELETED]
        return sorted(snapshots, key=lambda s: s.created_at, reverse=True)

    def get_latest_snapshot(self, snapshot_type: Optional[SnapshotType] = None) -> Optional[Snapshot]:
        snapshots = [s for s in self._snapshots.values()
                     if s.is_valid() and (snapshot_type is None or s.snapshot_type == snapshot_type)]
        if snapshots:
            return max(snapshots, key=lambda s: s.created_at)
        return None

    def create_recovery_point(self, description: str = "", is_auto: bool = False) -> RecoveryPoint:
        point = RecoveryPoint(description=description, is_auto=is_auto)
        self._recovery_points.append(point)
        return point

    def get_recovery_points(self) -> List[RecoveryPoint]:
        return sorted(self._recovery_points, key=lambda p: p.timestamp, reverse=True)

    def check_auto_snapshot_needed(self) -> bool:
        return time.time() - self._last_auto_snapshot > self.AUTO_SNAPSHOT_INTERVAL

    def perform_auto_snapshot(self) -> Optional[Snapshot]:
        if self.check_auto_snapshot_needed():
            snapshot = self.create_snapshot(
                name=f"auto_{int(time.time())}",
                snapshot_type=SnapshotType.INCREMENTAL,
            )
            self._last_auto_snapshot = time.time()
            return snapshot
        return None

    def verify_snapshot(self, snapshot_id: str) -> bool:
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False

        checksum_data = f"{snapshot_id}:{snapshot.size_bytes}:{len(snapshot.included_inodes)}".encode()
        expected = hashlib.sha256(checksum_data).hexdigest()

        if snapshot.checksum != expected:
            snapshot.status = SnapshotStatus.CORRUPTED
            return False

        return True

    def repair_snapshot(self, snapshot_id: str) -> bool:
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            return False

        if snapshot.status == SnapshotStatus.CORRUPTED:
            checksum_data = f"{snapshot_id}:{snapshot.size_bytes}:{len(snapshot.included_inodes)}".encode()
            snapshot.checksum = hashlib.sha256(checksum_data).hexdigest()
            snapshot.status = SnapshotStatus.COMPLETE
            return True

        return False

    def get_snapshot_chain(self, snapshot_id: str) -> List[Snapshot]:
        chain = []
        current_id = snapshot_id

        while current_id:
            snapshot = self._snapshots.get(current_id)
            if not snapshot:
                break
            chain.append(snapshot)
            current_id = snapshot.parent_id

        return list(reversed(chain))

    def _cleanup_old_snapshots(self) -> None:
        snapshots = sorted(self._snapshots.values(), key=lambda s: s.created_at)
        while len(snapshots) > self.MAX_SNAPSHOTS // 2:
            oldest = snapshots.pop(0)
            self.delete_snapshot(oldest.id)

    def _add_recovery_point(self, snapshot_id: str, description: str) -> None:
        point = RecoveryPoint(snapshot_id=snapshot_id, description=description)
        self._recovery_points.append(point)

    def get_storage_info(self) -> dict:
        total_size = sum(s.size_bytes for s in self._snapshots.values() if s.is_valid())
        return {
            "total_snapshots": len([s for s in self._snapshots.values() if s.status != SnapshotStatus.DELETED]),
            "total_size_bytes": total_size,
            "recovery_points": len(self._recovery_points),
        }
