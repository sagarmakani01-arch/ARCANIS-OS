"""06_ArcanisPackageManager — Declarative, intent-based package resolution."""

__version__ = "0.1.0"

from arcanis_pkg.resolver import PackageResolver, PackageIntent
from arcanis_pkg.registry import PackageRegistry, PackageInfo

__all__ = ["PackageResolver", "PackageIntent", "PackageRegistry", "PackageInfo"]
