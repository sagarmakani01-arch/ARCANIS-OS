"""ArcanisFileSystem Backup Utility.

Provides backup and restore operations.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.filesystem import ArcanisFileSystem
from security.recovery import SnapshotType


class BackupManager:
    """Manages filesystem backup operations."""

    def __init__(self, fs: ArcanisFileSystem):
        self.fs = fs
        self.backup_history = []

    def create_backup(self, name: str = "", backup_type: str = "full") -> dict:
        snapshot_type = SnapshotType.FULL if backup_type == "full" else SnapshotType.INCREMENTAL

        start_time = time.time()
        snap = self.fs.snapshot(name=name or f"backup_{int(time.time())}", snapshot_type=snapshot_type)
        duration = time.time() - start_time

        backup_info = {
            "id": snap.id,
            "name": snap.name,
            "type": backup_type,
            "timestamp": snap.created_at,
            "size": snap.size_bytes,
            "duration": duration,
            "status": "complete",
        }

        self.backup_history.append(backup_info)
        return backup_info

    def list_backups(self) -> list:
        return self.backup_history

    def get_backup(self, backup_id: str) -> dict:
        for backup in self.backup_history:
            if backup["id"] == backup_id:
                return backup
        return {}

    def export_metadata(self, filepath: str) -> int:
        metadata = {
            "filesystem_info": self.fs.get_info(),
            "backup_history": self.backup_history,
            "snapshots": [s.to_dict() for s in self.fs._recovery.list_snapshots()],
            "export_time": time.time(),
        }

        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=2)

        return len(self.backup_history)


def main():
    if len(sys.argv) < 2:
        print("Usage: arcanis_backup.py <command> [args]")
        print("Commands:")
        print("  create [name] [type]")
        print("  list")
        print("  export <filepath>")
        return 1

    command = sys.argv[1]
    fs = ArcanisFileSystem()
    manager = BackupManager(fs)

    if command == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        backup_type = sys.argv[3] if len(sys.argv) > 3 else "full"
        info = manager.create_backup(name, backup_type)
        print(json.dumps(info, indent=2))

    elif command == "list":
        backups = manager.list_backups()
        print(json.dumps(backups, indent=2))

    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: arcanis_backup.py export <filepath>")
            return 1
        count = manager.export_metadata(sys.argv[2])
        print(f"Exported {count} backup records")

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
