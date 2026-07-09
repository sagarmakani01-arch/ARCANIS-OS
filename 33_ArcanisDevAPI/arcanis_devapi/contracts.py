from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class APIVersion(Enum):
    V1 = "1.0"
    V2 = "2.0"


@dataclass
class APIResponse:
    status: int = 200
    data: Any = None
    error: Optional[str] = None
    version: str = "1.0"
    timestamp: float = field(default_factory=time.time)
    request_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "version": self.version,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
        }


@dataclass
class APIEndpoint:
    path: str = ""
    method: str = "GET"
    description: str = ""
    version: APIVersion = APIVersion.V1
    handler: Optional[Callable] = None
    deprecated: bool = False
    rate_limit: int = 100
    requires_auth: bool = False
    schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class APIContract:
    name: str = "ArcanisDevAPI"
    version: APIVersion = APIVersion.V1
    description: str = ""
    base_url: str = "/api"
    endpoints: list[APIEndpoint] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    stable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version.value,
            "description": self.description,
            "base_url": self.base_url,
            "stable": self.stable,
            "endpoints": [
                {"path": e.path, "method": e.method, "description": e.description,
                 "deprecated": e.deprecated, "requires_auth": e.requires_auth}
                for e in self.endpoints
            ],
        }
