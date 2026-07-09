"""Arcanis Assets — static assets, templates, and resource management."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Asset:
    asset_id: str = ""
    name: str = ""
    category: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class Template:
    template_id: str = ""
    name: str = ""
    description: str = ""
    content: str = ""
    variables: list[str] = field(default_factory=list)
    category: str = ""


class AssetRegistry:
    def __init__(self):
        self._assets: dict[str, Asset] = {}
        self._templates: dict[str, Template] = {}
        self._counter = 0

    def register_asset(self, name: str, category: str = "", path: str = "",
                       mime_type: str = "", metadata: dict[str, Any] | None = None) -> str:
        self._counter += 1
        asset_id = f"asset_{self._counter:04d}"
        self._assets[asset_id] = Asset(
            asset_id=asset_id, name=name, category=category,
            mime_type=mime_type, path=path, metadata=metadata or {},
        )
        return asset_id

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self._assets.get(asset_id)

    def search_assets(self, query: str) -> list[Asset]:
        query_lower = query.lower()
        return [a for a in self._assets.values()
                if query_lower in a.name.lower() or query_lower in a.category.lower()]

    def register_template(self, name: str, content: str, variables: list[str] | None = None,
                          description: str = "", category: str = "") -> str:
        template_id = f"tmpl_{name.lower().replace(' ', '_')}"
        self._templates[template_id] = Template(
            template_id=template_id, name=name, description=description,
            content=content, variables=variables or [], category=category,
        )
        return template_id

    def render_template(self, template_id: str, values: dict[str, str]) -> Optional[str]:
        template = self._templates.get(template_id)
        if not template:
            return None
        result = template.content
        for var in template.variables:
            result = result.replace(f"{{{var}}}", values.get(var, f"<{var}>"))
        return result

    def get_template(self, template_id: str) -> Optional[Template]:
        return self._templates.get(template_id)

    def list_templates(self, category: str = "") -> list[Template]:
        if category:
            return [t for t in self._templates.values() if t.category == category]
        return list(self._templates.values())

    def export_manifest(self) -> str:
        manifest = {
            "assets": {aid: {"name": a.name, "category": a.category, "mime_type": a.mime_type}
                       for aid, a in self._assets.items()},
            "templates": {tid: {"name": t.name, "category": t.category, "variables": t.variables}
                          for tid, t in self._templates.items()},
        }
        return json.dumps(manifest, indent=2)

    def get_stats(self) -> dict:
        categories = {}
        for a in self._assets.values():
            categories[a.category] = categories.get(a.category, 0) + 1
        return {"total_assets": len(self._assets), "total_templates": len(self._templates),
                "categories": categories}
