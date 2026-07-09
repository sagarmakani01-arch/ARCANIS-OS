"""Enterprise Security Certification — compliance framework, audit logging, policy enforcement."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class ComplianceStandard(Enum):
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    NIST = "nist"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    CUSTOM = "custom"


class CheckSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CheckResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class AuditEntry:
    timestamp: float = 0.0
    event_type: str = ""
    actor: str = ""
    target: str = ""
    action: str = ""
    result: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    entry_hash: str = ""

    def compute_hash(self, prev_hash: str = "") -> str:
        data = f"{self.timestamp}{self.event_type}{self.actor}{self.target}{self.action}{self.result}{prev_hash}"
        self.entry_hash = hashlib.sha256(data.encode()).hexdigest()[:16]
        return self.entry_hash


@dataclass
class ComplianceCheck:
    check_id: str = ""
    name: str = ""
    description: str = ""
    standard: ComplianceStandard = ComplianceStandard.CUSTOM
    severity: CheckSeverity = CheckSeverity.MEDIUM
    check_fn: Optional[Callable] = None
    remediation: str = ""


@dataclass
class CheckRun:
    check_id: str = ""
    result: CheckResult = CheckResult.SKIP
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    policy_id: str = ""
    name: str = ""
    description: str = ""
    rules: list[dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    enforce: bool = True


class AuditLogger:
    def __init__(self):
        self._entries: list[AuditEntry] = []
        self._prev_hash: str = "genesis"

    def log(self, event_type: str, actor: str, target: str, action: str,
            result: str = "", metadata: dict[str, Any] | None = None) -> AuditEntry:
        entry = AuditEntry(
            timestamp=time.time(), event_type=event_type, actor=actor,
            target=target, action=action, result=result, metadata=metadata or {},
        )
        entry.compute_hash(self._prev_hash)
        self._prev_hash = entry.entry_hash
        self._entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        prev = "genesis"
        for entry in self._entries:
            expected = hashlib.sha256(
                f"{entry.timestamp}{entry.event_type}{entry.actor}{entry.target}"
                f"{entry.action}{entry.result}{prev}".encode()
            ).hexdigest()[:16]
            if entry.entry_hash != expected:
                return False
            prev = entry.entry_hash
        return True

    def query(self, event_type: str = "", actor: str = "", limit: int = 100) -> list[AuditEntry]:
        results = self._entries
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if actor:
            results = [e for e in results if e.actor == actor]
        return results[-limit:]

    def export_json(self) -> str:
        return json.dumps([
            {"ts": e.timestamp, "type": e.event_type, "actor": e.actor,
             "target": e.target, "action": e.action, "result": e.result,
             "hash": e.entry_hash}
            for e in self._entries
        ], indent=2)

    def count(self) -> int:
        return len(self._entries)


class ComplianceEngine:
    def __init__(self):
        self._checks: dict[str, ComplianceCheck] = {}
        self._results: list[CheckRun] = []
        self._policies: dict[str, Policy] = {}

    def register_check(self, check: ComplianceCheck) -> None:
        self._checks[check.check_id] = check

    def register_policy(self, policy: Policy) -> None:
        self._policies[policy.policy_id] = policy

    def run_check(self, check_id: str) -> CheckRun:
        check = self._checks.get(check_id)
        if not check:
            return CheckRun(check_id=check_id, result=CheckResult.SKIP, message="Check not found")

        run = CheckRun(check_id=check_id)
        try:
            if check.check_fn:
                passed = check.check_fn()
                run.result = CheckResult.PASS if passed else CheckResult.FAIL
            else:
                run.result = CheckResult.SKIP
                run.message = "No check function"
        except Exception as e:
            run.result = CheckResult.FAIL
            run.message = str(e)

        self._results.append(run)
        return run

    def run_all(self, standard: ComplianceStandard | None = None) -> list[CheckRun]:
        for check in self._checks.values():
            if standard and check.standard != standard:
                continue
            self.run_check(check.check_id)
        return self._results[-len(self._checks):]

    def evaluate_policy(self, policy_id: str, context: dict[str, Any]) -> dict[str, Any]:
        policy = self._policies.get(policy_id)
        if not policy:
            return {"allowed": False, "reason": "Policy not found"}
        if not policy.enabled:
            return {"allowed": True, "reason": "Policy disabled"}

        for rule in policy.rules:
            rule_type = rule.get("type", "")
            if rule_type == "deny_action" and context.get("action") == rule.get("action"):
                return {"allowed": False, "reason": f"Denied by rule: {rule.get('description', '')}"}
            if rule_type == "require_capability" and rule.get("capability") not in context.get("capabilities", []):
                return {"allowed": False, "reason": f"Missing capability: {rule.get('capability')}"}
            if rule_type == "max_value" and context.get(rule.get("metric", "")) > rule.get("limit", 0):
                return {"allowed": False, "reason": f"Exceeds limit: {rule.get('description', '')}"}

        return {"allowed": True, "reason": "All rules passed"}

    def summary(self) -> dict:
        results = {}
        for r in self._results:
            results[r.result.value] = results.get(r.result.value, 0) + 1
        return {
            "total_checks": len(self._checks),
            "checks_run": len(self._results),
            "results": results,
            "policies": len(self._policies),
        }


def create_default_checks() -> list[ComplianceCheck]:
    return [
        ComplianceCheck("ENT-001", "Capability enforcement", "All system calls require explicit capabilities",
                        ComplianceStandard.NIST, CheckSeverity.CRITICAL),
        ComplianceCheck("ENT-002", "Audit log integrity", "Audit log chain is unbroken",
                        ComplianceStandard.SOC2, CheckSeverity.CRITICAL),
        ComplianceCheck("ENT-003", "No hardcoded secrets", "No secrets in source code",
                        ComplianceStandard.OWASP, CheckSeverity.HIGH),
        ComplianceCheck("ENT-004", "Process isolation", "Each process runs in isolated address space",
                        ComplianceStandard.NIST, CheckSeverity.HIGH),
        ComplianceCheck("ENT-005", "Input validation", "All external inputs are validated",
                        ComplianceStandard.OWASP, CheckSeverity.HIGH),
        ComplianceCheck("ENT-006", "Least privilege", "Default deny, explicit grant",
                        ComplianceStandard.SOC2, CheckSeverity.MEDIUM),
        ComplianceCheck("ENT-007", "Data at rest encryption", "Sensitive data encrypted on disk",
                        ComplianceStandard.GDPR, CheckSeverity.MEDIUM),
        ComplianceCheck("ENT-008", "Data in transit encryption", "All network traffic encrypted",
                        ComplianceStandard.PCI_DSS, CheckSeverity.HIGH),
        ComplianceCheck("ENT-009", "Access logging", "All access attempts logged",
                        ComplianceStandard.SOC2, CheckSeverity.MEDIUM),
        ComplianceCheck("ENT-010", "Recovery procedures", "System can recover from failure",
                        ComplianceStandard.ISO27001, CheckSeverity.HIGH),
    ]
