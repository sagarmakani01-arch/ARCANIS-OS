from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Optional

from .capability import Capability, CapabilityScope, CapabilityToken


class SecurityPolicy:
    def __init__(self):
        self.deny_rules: list[dict[str, Any]] = []
        self.allow_rules: list[dict[str, Any]] = []
        self.rate_limits: dict[str, tuple[int, float]] = {}

    def add_deny(self, capability: Capability, pattern: str = "*") -> None:
        self.deny_rules.append({"capability": capability, "pattern": pattern})

    def add_allow(self, capability: Capability, pattern: str = "*") -> None:
        self.allow_rules.append({"capability": capability, "pattern": pattern})

    def set_rate_limit(self, capability: Capability, max_per_second: int) -> None:
        self.rate_limits[capability.value] = (max_per_second, 1.0)

    def check(self, token: CapabilityToken, resource: str) -> bool:
        for rule in self.deny_rules:
            if rule["capability"] == token.capability or rule["capability"] == Capability.ALL:
                if rule["pattern"] == "*" or rule["pattern"] in resource:
                    return False
        for rule in self.allow_rules:
            if rule["capability"] == token.capability or rule["capability"] == Capability.ALL:
                if rule["pattern"] == "*" or rule["pattern"] in resource:
                    return True
        return len(self.allow_rules) == 0


class AuditLog:
    def __init__(self):
        self._entries: list[dict[str, Any]] = []

    def record(self, action: str, token: CapabilityToken, resource: str,
               granted: bool, details: Optional[str] = None) -> None:
        self._entries.append({
            "timestamp": time.time(),
            "action": action,
            "token_id": token.token_id,
            "capability": token.capability.value,
            "subject": token.subject_id,
            "resource": resource,
            "granted": granted,
            "details": details,
        })

    def query(self, capability: Optional[str] = None, subject: Optional[str] = None,
              granted: Optional[bool] = None, limit: int = 100) -> list[dict[str, Any]]:
        results = self._entries
        if capability:
            results = [e for e in results if e["capability"] == capability]
        if subject:
            results = [e for e in results if e["subject"] == subject]
        if granted is not None:
            results = [e for e in results if e["granted"] == granted]
        return results[-limit:]

    def stats(self) -> dict[str, Any]:
        total = len(self._entries)
        granted = sum(1 for e in self._entries if e["granted"])
        denied = total - granted
        by_cap = defaultdict(int)
        for e in self._entries:
            by_cap[e["capability"]] += 1
        return {"total": total, "granted": granted, "denied": denied, "by_capability": dict(by_cap)}


class CapabilityManager:
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()
        self.audit = AuditLog()
        self._tokens: dict[str, CapabilityToken] = {}
        self._subject_tokens: dict[str, list[str]] = defaultdict(list)
        self._rate_counters: dict[str, list[float]] = defaultdict(list)

    def grant(self, capability: Capability, subject_id: str, resource: str = "*",
              expires_in: Optional[float] = None, max_uses: Optional[int] = None,
              constraints: Optional[dict[str, Any]] = None) -> CapabilityToken:
        token = CapabilityToken(
            capability=capability,
            scope=CapabilityScope.USER,
            subject_id=subject_id,
            resource_pattern=resource,
            expires_at=time.time() + expires_in if expires_in else None,
            max_uses=max_uses,
            constraints=constraints or {},
        )
        self._tokens[token.token_id] = token
        self._subject_tokens[subject_id].append(token.token_id)
        return token

    def revoke(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        if not token:
            return False
        token.revoked = True
        return True

    def delegate(self, parent_token_id: str, capability: Capability,
                 resource: str, expires_in: Optional[float] = None,
                 max_uses: Optional[int] = None) -> Optional[CapabilityToken]:
        parent = self._tokens.get(parent_token_id)
        if not parent or not parent.is_valid():
            return None
        try:
            child = parent.delegate(capability, resource, expires_in, max_uses)
            self._tokens[child.token_id] = child
            self._subject_tokens[parent.subject_id].append(child.token_id)
            return child
        except ValueError:
            return None

    def authorize(self, token_id: str, action: str, resource: str) -> bool:
        token = self._tokens.get(token_id)
        if not token or not token.is_valid():
            self.audit.record(action, token or CapabilityToken(), resource, False, "invalid_token")
            return False

        if not token.matches_resource(resource):
            self.audit.record(action, token, resource, False, "resource_mismatch")
            return False

        if not self.policy.check(token, resource):
            self.audit.record(action, token, resource, False, "policy_denied")
            return False

        if self._check_rate_limit(token):
            self.audit.record(action, token, resource, False, "rate_limited")
            return False

        token.consume()
        self.audit.record(action, token, resource, True)
        return True

    def _check_rate_limit(self, token: CapabilityToken) -> bool:
        limit_info = self.policy.rate_limits.get(token.capability.value)
        if not limit_info:
            return False
        max_per_sec, window = limit_info
        now = time.time()
        key = f"{token.token_id}:{token.capability.value}"
        timestamps = self._rate_counters[key]
        timestamps[:] = [t for t in timestamps if now - t < window]
        if len(timestamps) >= max_per_sec:
            return True
        timestamps.append(now)
        return False

    def get_tokens(self, subject_id: str) -> list[CapabilityToken]:
        token_ids = self._subject_tokens.get(subject_id, [])
        return [self._tokens[tid] for tid in token_ids if tid in self._tokens]

    def get_active_tokens(self, subject_id: str) -> list[CapabilityToken]:
        return [t for t in self.get_tokens(subject_id) if t.is_valid()]

    def cleanup_expired(self) -> int:
        expired = [tid for tid, t in self._tokens.items() if not t.is_valid()]
        for tid in expired:
            del self._tokens[tid]
        return len(expired)

    def export_tokens(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._tokens.values()]
