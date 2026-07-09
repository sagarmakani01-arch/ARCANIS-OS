"""General Availability Release — changelog, packaging, distribution pipeline."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ReleaseStage(Enum):
    DEVELOPMENT = "development"
    ALPHA = "alpha"
    BETA = "beta"
    RC = "release_candidate"
    GA = "general_availability"


class ChangeType(Enum):
    ADDED = "Added"
    CHANGED = "Changed"
    DEPRECATED = "Deprecated"
    REMOVED = "Removed"
    FIXED = "Fixed"
    SECURITY = "Security"


@dataclass
class Change:
    change_type: ChangeType = ChangeType.ADDED
    description: str = ""
    module: str = ""
    breaking: bool = False


@dataclass
class ReleaseNote:
    version: str = ""
    stage: ReleaseStage = ReleaseStage.DEVELOPMENT
    date: str = ""
    codename: str = ""
    changes: list[Change] = field(default_factory=list)
    migration_guide: str = ""
    known_issues: list[str] = field(default_factory=list)
    checksum: str = ""

    def compute_checksum(self) -> str:
        data = f"{self.version}{self.stage.value}{self.date}{self.codename}"
        for c in self.changes:
            data += f"{c.change_type.value}{c.description}{c.module}"
        self.checksum = hashlib.sha256(data.encode()).hexdigest()[:16]
        return self.checksum


@dataclass
class ModuleManifest:
    name: str = ""
    version: str = ""
    path: str = ""
    language: str = "python"
    dependencies: list[str] = field(default_factory=list)
    entry_point: str = ""


@dataclass
class DistributionPackage:
    package_id: str = ""
    name: str = ""
    version: str = ""
    files: list[str] = field(default_factory=list)
    size_bytes: int = 0
    checksum: str = ""
    created_at: float = field(default_factory=time.time)


class Changelog:
    def __init__(self):
        self._releases: list[ReleaseNote] = []

    def add_release(self, release: ReleaseNote) -> None:
        release.compute_checksum()
        self._releases.append(release)

    def get_latest(self) -> Optional[ReleaseNote]:
        return self._releases[-1] if self._releases else None

    def get_release(self, version: str) -> Optional[ReleaseNote]:
        for r in self._releases:
            if r.version == version:
                return r
        return None

    def generate_markdown(self) -> str:
        lines = ["# Changelog\n"]
        for release in reversed(self._releases):
            lines.append(f"## {release.version} ({release.date}) — {release.codename}\n")
            lines.append(f"**Stage:** {release.stage.value}  ")
            lines.append(f"**Checksum:** `{release.checksum}`\n")

            by_type: dict[str, list[Change]] = {}
            for c in release.changes:
                key = c.change_type.value
                if key not in by_type:
                    by_type[key] = []
                by_type[key].append(c)

            for change_type, changes in by_type.items():
                lines.append(f"### {change_type}\n")
                for c in changes:
                    prefix = "!" if c.breaking else "-"
                    module = f"**{c.module}**: " if c.module else ""
                    lines.append(f"{prefix} {module}{c.description}")

            if release.known_issues:
                lines.append("\n### Known Issues\n")
                for issue in release.known_issues:
                    lines.append(f"- {issue}")
            lines.append("")

        return "\n".join(lines)

    def export_json(self) -> str:
        return json.dumps([
            {"version": r.version, "stage": r.stage.value, "date": r.date,
             "codename": r.codename, "checksum": r.checksum,
             "changes": [{"type": c.change_type.value, "description": c.description,
                          "module": c.module, "breaking": c.breaking} for c in r.changes],
             "known_issues": r.known_issues}
            for r in self._releases
        ], indent=2)


class ReleasePipeline:
    def __init__(self):
        self._modules: dict[str, ModuleManifest] = {}
        self._packages: list[DistributionPackage] = []
        self._changelog = Changelog()
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def register_module(self, manifest: ModuleManifest) -> None:
        self._modules[manifest.name] = manifest

    def create_release(self, version: str, stage: ReleaseStage, codename: str = "",
                       date: str = "", changes: list[Change] | None = None,
                       known_issues: list[str] | None = None) -> ReleaseNote:
        release = ReleaseNote(
            version=version, stage=stage, date=date or time.strftime("%Y-%m-%d"),
            codename=codename, changes=changes or [], known_issues=known_issues or [],
        )
        release.compute_checksum()
        self._changelog.add_release(release)
        return release

    def build_package(self, version: str) -> DistributionPackage:
        files = []
        total_size = 0
        for name, manifest in self._modules.items():
            files.append(manifest.path)
            total_size += len(manifest.path) * 100  # estimate

        pkg = DistributionPackage(
            package_id=f"pkg_{version.replace('.', '_')}",
            name="arcanis", version=version, files=files,
            size_bytes=total_size,
        )
        data = f"{pkg.package_id}{pkg.version}{len(files)}"
        pkg.checksum = hashlib.sha256(data.encode()).hexdigest()[:16]
        self._packages.append(pkg)
        return pkg

    def get_changelog(self) -> Changelog:
        return self._changelog

    def list_modules(self) -> list[ModuleManifest]:
        return list(self._modules.values())

    def get_status(self) -> dict:
        latest = self._changelog.get_latest()
        return {
            "initialized": self._initialized,
            "modules_registered": len(self._modules),
            "releases": len(self._changelog._releases),
            "packages_built": len(self._packages),
            "latest_version": latest.version if latest else None,
            "latest_stage": latest.stage.value if latest else None,
        }
