from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .registry import PackageInfo, PackageRegistry


@dataclass
class PackageIntent:
    intent: str = ""
    description: str = ""
    keywords: list[str] = None
    category: Optional[str] = None
    min_version: str = ""
    exclude: list[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.exclude is None:
            self.exclude = []


@dataclass
class ResolutionResult:
    packages: list[PackageInfo]
    intent: PackageIntent
    confidence: float
    reasoning: str
    install_order: list[str]


class PackageResolver:
    def __init__(self, registry: Optional[PackageRegistry] = None):
        self.registry = registry or PackageRegistry()
        self._resolution_history: list[ResolutionResult] = []

    def resolve(self, intent: PackageIntent) -> ResolutionResult:
        candidates: list[tuple[PackageInfo, float]] = []

        all_packages = self.registry.list_all()
        for pkg in all_packages:
            if pkg.name in intent.exclude:
                continue
            score = self._score_package(pkg, intent)
            if score > 0:
                candidates.append((pkg, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        selected = [c[0] for c in candidates[:10]]

        all_deps: set[str] = set()
        for pkg in selected:
            for dep in pkg.dependencies:
                all_deps.add(dep)
        for dep_name in all_deps:
            dep_pkg = self.registry.get(dep_name)
            if dep_pkg and dep_pkg not in selected:
                selected.append(dep_pkg)

        install_order = self._topo_sort(selected)

        confidence = min(candidates[0][1] / 10.0, 1.0) if candidates else 0.0
        reasoning = self._build_reasoning(selected, intent)

        result = ResolutionResult(
            packages=selected, intent=intent,
            confidence=confidence, reasoning=reasoning,
            install_order=install_order,
        )
        self._resolution_history.append(result)
        return result

    def resolve_from_text(self, text: str) -> ResolutionResult:
        intent = self._parse_natural_language(text)
        return self.resolve(intent)

    def _score_package(self, pkg: PackageInfo, intent: PackageIntent) -> float:
        score = 0.0
        text = (pkg.name + " " + pkg.description + " " + " ".join(pkg.tags)).lower()

        if intent.intent:
            for word in intent.intent.lower().split():
                if word in text:
                    score += 2.0

        if intent.keywords:
            for kw in intent.keywords:
                if kw.lower() in text:
                    score += 1.5

        if intent.category and pkg.category == intent.category:
            score += 3.0

        for kw in (intent.keywords or []):
            for ikw in pkg.intent_keywords:
                if kw.lower() in ikw.lower():
                    score += 2.0

        return score

    def _parse_natural_language(self, text: str) -> PackageIntent:
        keywords = text.lower().split()
        category = None
        cat_map = {
            "web": "networking", "server": "networking", "http": "networking",
            "ai": "ai", "ml": "ai", "inference": "ai",
            "db": "data", "database": "data", "query": "data",
            "gui": "interface", "ui": "interface", "window": "interface",
            "test": "development", "build": "development", "compile": "development",
            "sec": "security", "crypto": "security", "auth": "security",
        }
        for kw in keywords:
            if kw in cat_map:
                category = cat_map[kw]
                break

        return PackageIntent(
            intent=text, description=text,
            keywords=keywords, category=category,
        )

    def _topo_sort(self, packages: list[PackageInfo]) -> list[str]:
        name_to_pkg = {p.name: p for p in packages}
        in_degree: dict[str, int] = {p.name: 0 for p in packages}
        for pkg in packages:
            for dep in pkg.dependencies:
                if dep in in_degree:
                    in_degree[pkg.name] += 1

        queue = [n for n, d in in_degree.items() if d == 0]
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for pkg in packages:
                if node in pkg.dependencies and pkg.name in in_degree:
                    in_degree[pkg.name] -= 1
                    if in_degree[pkg.name] == 0:
                        queue.append(pkg.name)

        for pkg in packages:
            if pkg.name not in order:
                order.append(pkg.name)
        return order

    def _build_reasoning(self, packages: list[PackageInfo], intent: PackageIntent) -> str:
        if not packages:
            return f"No packages found matching intent: {intent.intent}"
        names = [p.name for p in packages[:5]]
        return f"Resolved {len(packages)} packages for '{intent.intent}': {', '.join(names)}{'...' if len(packages) > 5 else ''}"

    def get_history(self) -> list[ResolutionResult]:
        return list(self._resolution_history)
