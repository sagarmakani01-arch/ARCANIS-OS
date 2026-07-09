from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PackageInfo:
    name: str = ""
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    license: str = ""
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    category: str = ""
    intent_keywords: list[str] = field(default_factory=list)
    source_url: str = ""
    installed: bool = False
    install_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name, "version": self.version,
            "description": self.description, "author": self.author,
            "dependencies": self.dependencies, "tags": self.tags,
            "category": self.category, "installed": self.installed,
        }


class PackageRegistry:
    def __init__(self):
        self._packages: dict[str, PackageInfo] = {}
        self._seed_packages()

    def _seed_packages(self) -> None:
        pkgs = [
            PackageInfo(name="arcanis-core", version="1.0.0",
                        description="Core Arcanis runtime libraries",
                        tags=["runtime", "core", "essential"], category="system",
                        intent_keywords=["runtime", "core", "base"]),
            PackageInfo(name="arcanis-dev", version="1.0.0",
                        description="Development tools and compilers",
                        tags=["dev", "compiler", "build"], category="development",
                        intent_keywords=["develop", "compile", "build", "code"]),
            PackageInfo(name="arcanis-ai", version="0.5.0",
                        description="AI inference and model management",
                        tags=["ai", "ml", "inference"], category="ai",
                        intent_keywords=["ai", "inference", "model", "machine learning"]),
            PackageInfo(name="arcanis-web", version="0.3.0",
                        description="Web server and HTTP client libraries",
                        tags=["web", "http", "server"], category="networking",
                        intent_keywords=["web", "http", "server", "api"]),
            PackageInfo(name="arcanis-db", version="0.4.0",
                        description="Database engine and query tools",
                        tags=["database", "storage", "query"], category="data",
                        intent_keywords=["database", "storage", "query", "sql"]),
            PackageInfo(name="arcanis-sec", version="0.6.0",
                        description="Security and cryptography libraries",
                        tags=["security", "crypto", "auth"], category="security",
                        intent_keywords=["security", "encrypt", "auth", "ssl"]),
            PackageInfo(name="arcanis-gui", version="0.2.0",
                        description="GUI framework and UI components",
                        tags=["gui", "ui", "components"], category="interface",
                        intent_keywords=["gui", "ui", "window", "button"]),
            PackageInfo(name="arcanis-test", version="0.1.0",
                        description="Testing framework and utilities",
                        tags=["testing", "test", "assert"], category="development",
                        intent_keywords=["test", "assert", "mock", "coverage"]),
            PackageInfo(name="arcanis-net", version="0.3.0",
                        description="Networking stack and protocols",
                        tags=["network", "tcp", "udp"], category="networking",
                        intent_keywords=["network", "tcp", "socket", "connect"]),
            PackageInfo(name="arcanis-fs", version="0.2.0",
                        description="Filesystem utilities and semantic indexing",
                        tags=["filesystem", "files", "index"], category="system",
                        intent_keywords=["file", "directory", "search", "index"]),
        ]
        for p in pkgs:
            self._packages[p.name] = p

    def search(self, query: str) -> list[PackageInfo]:
        query_lower = query.lower()
        results: list[tuple[PackageInfo, float]] = []
        for pkg in self._packages.values():
            score = 0.0
            if query_lower in pkg.name.lower():
                score += 3.0
            if query_lower in pkg.description.lower():
                score += 2.0
            for tag in pkg.tags:
                if query_lower in tag.lower():
                    score += 1.5
            for kw in pkg.intent_keywords:
                if query_lower in kw.lower():
                    score += 2.0
            if score > 0:
                results.append((pkg, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]

    def get(self, name: str) -> Optional[PackageInfo]:
        return self._packages.get(name)

    def list_all(self) -> list[PackageInfo]:
        return list(self._packages.values())

    def list_installed(self) -> list[PackageInfo]:
        return [p for p in self._packages.values() if p.installed]

    def register(self, pkg: PackageInfo) -> None:
        self._packages[pkg.name] = pkg

    def get_stats(self) -> dict:
        return {
            "total": len(self._packages),
            "installed": sum(1 for p in self._packages.values() if p.installed),
            "categories": list(set(p.category for p in self._packages.values())),
        }
