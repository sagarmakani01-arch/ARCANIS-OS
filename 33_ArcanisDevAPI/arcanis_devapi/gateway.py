from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Any, Callable, Optional

from .contracts import APIContract, APIEndpoint, APIResponse, APIVersion


class RateLimiter:
    def __init__(self):
        self._counts: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, limit: int, window: float = 1.0) -> bool:
        now = time.time()
        self._counts[key] = [t for t in self._counts[key] if now - t < window]
        if len(self._counts[key]) >= limit:
            return False
        self._counts[key].append(now)
        return True


class APIGateway:
    def __init__(self):
        self._contracts: dict[str, APIContract] = {}
        self._routes: dict[str, APIEndpoint] = {}
        self._middleware: list[Callable] = []
        self._rate_limiter = RateLimiter()
        self._request_log: list[dict[str, Any]] = []
        self._initialized = False

    def initialize(self) -> None:
        self._register_v1_contracts()
        self._initialized = True

    def _register_v1_contracts(self) -> None:
        v1 = APIContract(
            name="ArcanisDevAPI",
            version=APIVersion.V1,
            description="Arcanis Developer API v1.0 — Stable contracts for ecosystem integration",
            base_url="/api/v1",
            stable=True,
            endpoints=[
                APIEndpoint(path="/status", method="GET", description="System status",
                           version=APIVersion.V1, requires_auth=False),
                APIEndpoint(path="/brain/chat", method="POST", description="Chat with ArcanisBrain",
                           version=APIVersion.V1, requires_auth=True, rate_limit=30),
                APIEndpoint(path="/brain/classify", method="POST", description="Classify intent",
                           version=APIVersion.V1, requires_auth=False, rate_limit=60),
                APIEndpoint(path="/shell/execute", method="POST", description="Execute shell command",
                           version=APIVersion.V1, requires_auth=True, rate_limit=20),
                APIEndpoint(path="/shell/suggest", method="GET", description="Get command suggestions",
                           version=APIVersion.V1, requires_auth=False, rate_limit=30),
                APIEndpoint(path="/fs/search", method="POST", description="Semantic file search",
                           version=APIVersion.V1, requires_auth=False, rate_limit=30),
                APIEndpoint(path="/fs/index", method="POST", description="Index directory",
                           version=APIVersion.V1, requires_auth=True, rate_limit=10),
                APIEndpoint(path="/security/events", method="GET", description="Security event log",
                           version=APIVersion.V1, requires_auth=True, rate_limit=60),
                APIEndpoint(path="/security/anomalies", method="GET", description="Detected anomalies",
                           version=APIVersion.V1, requires_auth=True, rate_limit=30),
                APIEndpoint(path="/scheduler/plan", method="GET", description="AI scheduling plan",
                           version=APIVersion.V1, requires_auth=False, rate_limit=10),
                APIEndpoint(path="/packages/resolve", method="POST", description="Resolve packages by intent",
                           version=APIVersion.V1, requires_auth=False, rate_limit=20),
                APIEndpoint(path="/packages/search", method="GET", description="Search packages",
                           version=APIVersion.V1, requires_auth=False, rate_limit=30),
            ],
        )
        self._contracts["v1"] = v1
        for ep in v1.endpoints:
            key = f"{ep.method}:{v1.base_url}{ep.path}"
            self._routes[key] = ep

    def register_route(self, contract: APIContract, endpoint: APIEndpoint) -> None:
        key = f"{endpoint.method}:{contract.base_url}{endpoint.path}"
        self._routes[key] = endpoint

    def handle_request(self, method: str, path: str, data: Optional[dict] = None,
                       auth_token: Optional[str] = None) -> APIResponse:
        request_id = str(uuid.uuid4())[:8]
        key = f"{method}:{path}"
        endpoint = self._routes.get(key)

        if not endpoint:
            return APIResponse(status=404, error=f"Not found: {method} {path}", request_id=request_id)

        if endpoint.deprecated:
            return APIResponse(status=410, error=f"Endpoint deprecated: {method} {path}", request_id=request_id)

        if not self._rate_limiter.check(key, endpoint.rate_limit):
            return APIResponse(status=429, error="Rate limit exceeded", request_id=request_id)

        if endpoint.requires_auth and not auth_token:
            return APIResponse(status=401, error="Authentication required", request_id=request_id)

        self._request_log.append({
            "request_id": request_id, "method": method, "path": path,
            "timestamp": time.time(), "status": 200,
        })

        if endpoint.handler:
            try:
                result = endpoint.handler(data or {})
                return APIResponse(data=result, request_id=request_id, version="1.0")
            except Exception as e:
                return APIResponse(status=500, error=str(e), request_id=request_id)

        return APIResponse(data={"message": f"Endpoint {method} {path} acknowledged"}, request_id=request_id)

    def get_contract(self, version: str = "v1") -> Optional[APIContract]:
        return self._contracts.get(version)

    def list_endpoints(self) -> list[dict[str, Any]]:
        return [
            {"method": ep.method, "path": f"{self._contracts['v1'].base_url}{ep.path}",
             "description": ep.description, "auth_required": ep.requires_auth,
             "deprecated": ep.deprecated}
            for ep in self._routes.values()
        ]

    def get_stats(self) -> dict:
        return {
            "initialized": self._initialized,
            "contracts": len(self._contracts),
            "routes": len(self._routes),
            "total_requests": len(self._request_log),
            "request_log_limit": len(self._request_log),
        }
