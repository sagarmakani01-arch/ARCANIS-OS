import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime

from .communication import MessageBus


class ApprovalWorkflow:
    def __init__(self, action_id, requester, action, resource, context=None, risk_level="medium"):
        self.id = action_id
        self.requester = requester
        self.action = action
        self.resource = resource
        self.context = context or {}
        self.risk_level = risk_level
        self.status = "pending"
        self.approver = None
        self.reason = None
        self.created = time.time()
        self.decided = None

    def approve(self, approver, reason="Approved"):
        self.status = "approved"
        self.approver = approver
        self.reason = reason
        self.decided = time.time()

    def deny(self, approver, reason="Denied"):
        self.status = "denied"
        self.approver = approver
        self.reason = reason
        self.decided = time.time()

    def to_dict(self):
        return {
            "id": self.id,
            "requester": self.requester,
            "action": self.action,
            "resource": self.resource,
            "risk_level": self.risk_level,
            "status": self.status,
            "approver": self.approver,
            "reason": self.reason,
            "created": self.created,
            "decided": self.decided,
        }


class OversightLayer:
    def __init__(self, bus=None):
        self.bus = bus or MessageBus()
        self._workflows = {}
        self._approval_lock = threading.RLock()
        self._auto_approve_low_risk = True
        self._auto_approve_threshold = 0.7
        self._audit_log = []

        self._subscribe_events()

    def _subscribe_events(self):
        self.bus.subscribe("task.delegate", self._on_task_delegated)
        self.bus.subscribe("knowledge.updated", self._on_knowledge_updated)
        self.bus.subscribe("agent.activated", self._on_agent_activated)

    def _on_task_delegated(self, msg):
        if self._needs_approval(msg):
            sender = msg.get("sender", "unknown")
            payload = msg.get("payload", {})
            action = msg.get("task_type", "task")
            wf = self.request_approval(sender, action, msg.get("recipient", "unknown"), {
                "task_type": action, "payload_keys": list(payload.keys()),
            })
            if wf.status == "denied":
                self.bus.reply(msg, {"status": "denied", "reason": wf.reason})

    def _on_knowledge_updated(self, msg):
        payload = msg.get("payload", {})
        if payload.get("importance", 0) > 0.8:
            self._audit("knowledge", "high_importance_update", msg.get("sender"), payload)

    def _on_agent_activated(self, msg):
        payload = msg.get("payload", {})
        self._audit("agent", "activation", msg.get("sender"), payload)

    def _needs_approval(self, msg):
        priority = msg.get("priority", 5)
        risk_score = self._calculate_risk(msg)
        if self._auto_approve_low_risk and risk_score < self._auto_approve_threshold:
            return False
        return risk_score > 0.5

    def _calculate_risk(self, msg):
        risk = 0.0
        priority = msg.get("priority", 5)
        risk += priority / 10.0
        task_type = msg.get("task_type", "")
        high_risk_tasks = ["delete", "shutdown", "modify", "approve", "broadcast"]
        if any(t in task_type.lower() for t in high_risk_tasks):
            risk += 0.3
        sender = msg.get("sender", "")
        if sender == "unknown" or sender == "":
            risk += 0.2
        return min(risk, 1.0)

    def request_approval(self, requester, action, resource, context=None, risk_level="medium"):
        with self._approval_lock:
            wf_id = str(uuid.uuid4())[:8]
            wf = ApprovalWorkflow(wf_id, requester, action, resource, context, risk_level)

            if self._auto_approve_low_risk and risk_level == "low":
                wf.approve("system (auto)", "Low risk, auto-approved")
            else:
                self._workflows[wf_id] = wf
                self.bus.broadcast("oversight", MessageBus.APPROVAL_REQUESTED, wf.to_dict())
                self._audit("approval", "requested", requester, wf.to_dict())

            return wf

    def approve(self, workflow_id, approver, reason="Approved"):
        with self._approval_lock:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return False
            wf.approve(approver, reason)
            self.bus.broadcast("oversight", MessageBus.APPROVAL_GRANTED, wf.to_dict())
            self._audit("approval", "granted", approver, {"workflow_id": workflow_id, "reason": reason})
            del self._workflows[workflow_id]
            return True

    def deny(self, workflow_id, approver, reason="Denied"):
        with self._approval_lock:
            wf = self._workflows.get(workflow_id)
            if not wf:
                return False
            wf.deny(approver, reason)
            self.bus.broadcast("oversight", MessageBus.APPROVAL_DENIED, wf.to_dict())
            self._audit("approval", "denied", approver, {"workflow_id": workflow_id, "reason": reason})
            del self._workflows[workflow_id]
            return True

    def get_pending_approvals(self):
        return [wf.to_dict() for wf in self._workflows.values() if wf.status == "pending"]

    def search_audit(self, action_type="", limit=100):
        if action_type:
            return [e for e in self._audit_log if e["action_type"] == action_type][-limit:]
        return self._audit_log[-limit:]

    def _audit(self, category, action_type, actor, details=None):
        entry = {
            "timestamp": time.time(),
            "category": category,
            "action_type": action_type,
            "actor": actor,
            "details": details,
        }
        self._audit_log.append(entry)
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

    def explain(self, workflow_id):
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        lines = [
            f"=== Decision Explanation ===",
            f"Workflow: {wf.id}",
            f"Requester: {wf.requester}",
            f"Action: {wf.action} on {wf.resource}",
            f"Risk Level: {wf.risk_level}",
            f"Status: {wf.status}",
        ]
        if wf.status != "pending":
            lines.append(f"Decision: {wf.status.upper()} by {wf.approver}")
            lines.append(f"Reason: {wf.reason}")
            elapsed = wf.decided - wf.created
            lines.append(f"Decision Time: {elapsed:.1f}s")
        lines.append("")
        lines.append("Risk Factors:")
        risk = self._calculate_risk({"priority": 5, "task_type": wf.action, "sender": wf.requester})
        lines.append(f"  - Composite Risk Score: {risk:.2f}")
        if "reason" in wf.context:
            lines.append(f"  - Context: {wf.context['reason']}")
        return "\n".join(lines)

    def rollback(self, workflow_id, actor):
        wf = self._workflows.get(workflow_id)
        if not wf or wf.status != "approved":
            return False
        wf.status = "rolled_back"
        wf.approver = actor
        wf.reason = "Rolled back"
        self._audit("rollback", "executed", actor, {"workflow_id": workflow_id, "original_action": wf.action})
        return True

    def get_stats(self):
        return {
            "pending_approvals": len([w for w in self._workflows.values() if w.status == "pending"]),
            "audit_entries": len(self._audit_log),
            "auto_approve_low_risk": self._auto_approve_low_risk,
        }
