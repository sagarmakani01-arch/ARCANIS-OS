from __future__ import annotations
import uuid
from typing import Any, Dict, Optional


class Node:
    def __init__(
        self,
        id: Optional[str] = None,
        type: str = "generic",
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.type = type
        self.properties = properties or {}

    def __repr__(self) -> str:
        return f"Node(id={self.id!r}, type={self.type!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def get(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.properties[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Node:
        return cls(
            id=data.get("id"),
            type=data.get("type", "generic"),
            properties=data.get("properties", {}),
        )
