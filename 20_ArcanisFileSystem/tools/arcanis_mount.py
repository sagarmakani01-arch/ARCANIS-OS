"""ArcanisFileSystem Mount Utility.

Provides mount/unmount operations for the filesystem.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.filesystem import ArcanisFileSystem
from storage.memory import MemoryBackend
from storage.disk import DiskBackend


class MountManager:
    """Manages filesystem mount operations."""

    def __init__(self):
        self._mounted_fs = {}
        self._mount_table_path = Path("/tmp/arcanis_mounts.json")

    def mount(self, source: str, mount_point: str, options: dict = None) -> ArcanisFileSystem:
        options = options or {}

        if mount_point in self._mounted_fs:
            raise RuntimeError(f"Already mounted: {mount_point}")

        backend_type = options.get("backend", "memory")

        if backend_type == "disk":
            backend = DiskBackend(
                path=source,
                block_size=options.get("block_size", 4096),
                total_blocks=options.get("total_blocks", 1048576),
            )
        else:
            backend = MemoryBackend(
                block_size=options.get("block_size", 4096),
                total_blocks=options.get("total_blocks", 100000),
            )

        fs = ArcanisFileSystem(
            storage_backend=backend,
            mount_point=mount_point,
            enable_ai=options.get("ai", True),
        )

        self._mounted_fs[mount_point] = {
            "fs": fs,
            "source": source,
            "options": options,
        }

        print(f"Mounted {source} at {mount_point}")
        return fs

    def unmount(self, mount_point: str) -> bool:
        if mount_point not in self._mounted_fs:
            raise RuntimeError(f"Not mounted: {mount_point}")

        mount_info = self._mounted_fs[mount_point]
        mount_info["fs"].unmount()

        del self._mounted_fs[mount_point]
        print(f"Unmounted {mount_point}")
        return True

    def get_filesystem(self, mount_point: str) -> ArcanisFileSystem:
        if mount_point not in self._mounted_fs:
            raise RuntimeError(f"Not mounted: {mount_point}")
        return self._mounted_fs[mount_point]["fs"]

    def list_mounts(self) -> list:
        mounts = []
        for mount_point, info in self._mounted_fs.items():
            mounts.append({
                "mount_point": mount_point,
                "source": info["source"],
                "options": info["options"],
                "info": info["fs"].get_info(),
            })
        return mounts

    def is_mounted(self, mount_point: str) -> bool:
        return mount_point in self._mounted_fs


def main():
    if len(sys.argv) < 2:
        print("Usage: arcanis_mount.py <command> [args]")
        print("Commands:")
        print("  mount <source> <mount_point> [options]")
        print("  unmount <mount_point>")
        print("  list")
        return 1

    command = sys.argv[1]
    manager = MountManager()

    if command == "mount":
        if len(sys.argv) < 4:
            print("Usage: arcanis_mount.py mount <source> <mount_point>")
            return 1

        source = sys.argv[2]
        mount_point = sys.argv[3]
        options = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}

        fs = manager.mount(source, mount_point, options)
        info = fs.get_info()
        print(json.dumps(info, indent=2))

    elif command == "unmount":
        if len(sys.argv) < 3:
            print("Usage: arcanis_mount.py unmount <mount_point>")
            return 1

        mount_point = sys.argv[2]
        manager.unmount(mount_point)

    elif command == "list":
        mounts = manager.list_mounts()
        print(json.dumps(mounts, indent=2))

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
