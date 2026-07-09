from __future__ import annotations
import uuid
from typing import Any, Dict, Optional


class Relationship:
    def __init__(
        self,
        source_id: str,
        target_id: str,
        type: str = "related_to",
        id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.source_id = source_id
        self.target_id = target_id
        self.type = type
        self.properties = properties or {}

    def __repr__(self) -> str:
        return (
            f"Relationship(id={self.id!r}, {self.source_id!r} "
            f"-[{self.type}]-> {self.target_id!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Relationship):
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
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "properties": dict(self.properties),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Relationship:
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=data.get("type", "related_to"),
            id=data.get("id"),
            properties=data.get("properties", {}),
        )
