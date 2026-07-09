import pytest
from arcanis_pkg.resolver import PackageResolver, PackageIntent
from arcanis_pkg.registry import PackageRegistry, PackageInfo


class TestPackageRegistry:
    def setup_method(self):
        self.registry = PackageRegistry()

    def test_seed_packages(self):
        assert len(self.registry.list_all()) >= 10

    def test_search(self):
        results = self.registry.search("ai")
        assert len(results) >= 1
        assert any("ai" in p.name.lower() or "ai" in " ".join(p.tags).lower() for p in results)

    def test_get(self):
        pkg = self.registry.get("arcanis-core")
        assert pkg is not None
        assert pkg.version == "1.0.0"

    def test_register(self):
        self.registry.register(PackageInfo(name="custom-pkg", version="0.1.0"))
        assert self.registry.get("custom-pkg") is not None


class TestPackageResolver:
    def setup_method(self):
        self.resolver = PackageResolver()

    def test_resolve_by_keyword(self):
        intent = PackageIntent(intent="web server", keywords=["web", "http"])
        result = self.resolver.resolve(intent)
        assert len(result.packages) > 0
        assert result.confidence > 0

    def test_resolve_from_text(self):
        result = self.resolver.resolve_from_text("I need a database for my project")
        assert len(result.packages) > 0

    def test_install_order(self):
        intent = PackageIntent(intent="ai", keywords=["ai"])
        result = self.resolver.resolve(intent)
        assert isinstance(result.install_order, list)
        assert len(result.install_order) > 0

    def test_exclude(self):
        intent = PackageIntent(intent="ai", keywords=["ai"], exclude=["arcanis-ai"])
        result = self.resolver.resolve(intent)
        assert all(p.name != "arcanis-ai" for p in result.packages)
