import shutil
import os
import json
import datetime
from pathlib import Path
from typing import Optional


class BackupManager:
    def __init__(self, db):
        self.db = db

    def backup(self, path: Optional[str] = None) -> str:
        if self.db.path == ":memory:":
            raise ValueError("Cannot backup in-memory database. Use a file-based database.")

        if path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base = Path(self.db.path)
            path = str(base.parent / f"{base.stem}_backup_{timestamp}{base.suffix}")

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        self.db.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        with self.db._lock:
            shutil.copy2(self.db.path, target)

            wal_path = self.db.path + "-wal"
            if os.path.exists(wal_path):
                shutil.copy2(wal_path, str(target) + "-wal")

            shm_path = self.db.path + "-shm"
            if os.path.exists(shm_path):
                shm_target = str(target) + "-shm"
                shutil.copy2(shm_path, shm_target)

        return str(target)

    def restore(self, backup_path: str) -> str:
        if self.db.path == ":memory:":
            raise ValueError("Cannot restore to in-memory database. Use a file-based database.")

        backup = Path(backup_path)
        if not backup.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        self.db.conn.close()
        if hasattr(self.db._local, "conn"):
            self.db._local.conn = None

        with self.db._lock:
            shutil.copy2(backup_path, self.db.path)

        conn = self.db.conn
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return f"Restored from {backup_path}"

    def info(self) -> dict:
        if self.db.path == ":memory:":
            return {"path": ":memory:", "size": 0, "backupable": False}

        path = Path(self.db.path)
        if path.exists():
            return {
                "path": str(path),
                "size": path.stat().st_size,
                "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "backupable": True,
                "wal_exists": Path(str(path) + "-wal").exists(),
            }
        return {"path": str(path), "size": 0, "backupable": False}
