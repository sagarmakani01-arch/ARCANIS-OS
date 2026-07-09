"""ArcanisFileSystem Check (fsck) Tool.

Verifies filesystem integrity and repairs common issues.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.filesystem import ArcanisFileSystem
from core.inode import InodeType
from storage.memory import MemoryBackend


class FileSystemCheck:
    """Filesystem integrity checker."""

    def __init__(self, fs: ArcanisFileSystem):
        self.fs = fs
        self.errors = []
        self.warnings = []
        self.fixes = []

    def run_full_check(self) -> dict:
        print("ArcanisFileSystem Check (fsck) v1.0.0")
        print("=" * 50)

        self._check_inodes()
        self._check_directories()
        self._check_blocks()
        self._check_orphans()
        self._check_permissions()
        self._check_metadata()

        return self._generate_report()

    def _check_inodes(self) -> None:
        print("\n[1/6] Checking inodes...")

        for inode in self.fs._inodes.all_inodes():
            if inode.size < 0:
                self.errors.append(f"Inode {inode.id}: negative size ({inode.size})")

            if inode.inode_type == InodeType.FILE and not inode.block_pointers and inode.size > 0:
                self.errors.append(f"Inode {inode.id}: file has size but no blocks")

            if inode.inode_type == InodeType.DIRECTORY and inode.block_pointers:
                self.warnings.append(f"Inode {inode.id}: directory has block pointers")

            if inode.reference_count < 0:
                self.errors.append(f"Inode {inode.id}: negative reference count")

        print(f"   Found {self.fs._inodes.count()} inodes")

    def _check_directories(self) -> None:
        print("\n[2/6] Checking directories...")

        for inode in self.fs._inodes.find_by_type(InodeType.DIRECTORY):
            directory = self.fs._directories.get_directory(inode.id)
            if not directory:
                self.errors.append(f"Directory inode {inode.id}: no directory structure found")
                continue

            for entry in directory.list_entries():
                entry_inode = self.fs._inodes.get(entry.inode_id)
                if not entry_inode:
                    self.errors.append(f"Directory '{directory.inode_id}': entry '{entry.name}' points to missing inode {entry.inode_id}")

        print(f"   Checked {len(self.fs._inodes.find_by_type(InodeType.DIRECTORY))} directories")

    def _check_blocks(self) -> None:
        print("\n[3/6] Checking block allocations...")

        allocated_blocks = set()
        for inode in self.fs._inodes.all_inodes():
            for block_id in inode.block_pointers:
                if block_id in allocated_blocks:
                    self.errors.append(f"Block {block_id} allocated to multiple inodes")
                allocated_blocks.add(block_id)

        print(f"   Found {len(allocated_blocks)} allocated blocks")

    def _check_orphans(self) -> None:
        print("\n[4/6] Checking for orphaned inodes...")

        referenced_inodes = set()
        for directory in self.fs._directories._directories.values():
            for entry in directory.list_entries():
                referenced_inodes.add(entry.inode_id)

        orphans = []
        for inode in self.fs._inodes.all_inodes():
            if inode.id not in referenced_inodes and inode.id != self.fs._root_inode:
                orphans.append(inode)

        if orphans:
            self.warnings.append(f"Found {len(orphans)} orphaned inodes")

        print(f"   Found {len(orphans)} orphaned inodes")

    def _check_permissions(self) -> None:
        print("\n[5/6] Checking permissions...")

        issues = 0
        for inode in self.fs._inodes.all_inodes():
            if inode.permissions > 0o7777:
                self.errors.append(f"Inode {inode.id}: invalid permissions {oct(inode.permissions)}")
                issues += 1

        print(f"   Found {issues} permission issues")

    def _check_metadata(self) -> None:
        print("\n[6/6] Checking metadata...")

        for inode in self.fs._inodes.all_inodes():
            metadata = self.fs._metadata.get(inode.id)
            if not metadata:
                self.warnings.append(f"Inode {inode.id}: missing metadata")

        print(f"   Checked {self.fs._metadata.total_entries()} metadata entries")

    def _generate_report(self) -> dict:
        report = {
            "timestamp": time.time(),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "fixes": len(self.fixes),
            "error_details": self.errors,
            "warning_details": self.warnings,
            "fix_details": self.fixes,
            "status": "CLEAN" if not self.errors else "ERRORS FOUND",
        }

        print("\n" + "=" * 50)
        print("CHECK RESULTS:")
        print(f"  Errors:   {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Status:   {report['status']}")

        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")

        return report

    def repair(self) -> int:
        fixes = 0

        for inode in self.fs._inodes.all_inodes():
            if inode.size < 0:
                inode.size = 0
                fixes += 1

            if inode.reference_count < 0:
                inode.reference_count = 1
                fixes += 1

            if inode.permissions > 0o7777:
                inode.permissions = inode.permissions & 0o7777
                fixes += 1

        self.fixes.append(f"Applied {fixes} repairs")
        return fixes


def main():
    print("Initializing ArcanisFileSystem check...")
    fs = ArcanisFileSystem()
    checker = FileSystemCheck(fs)

    report = checker.run_full_check()

    if "--repair" in sys.argv:
        print("\nRunning repairs...")
        fixes = checker.repair()
        print(f"Applied {fixes} fixes")

    return 0 if report["status"] == "CLEAN" else 1


if __name__ == "__main__":
    sys.exit(main())
