import time
import uuid
from .kernel import IntelligenceKernel


class AgentSDK:
    def __init__(self, kernel=None):
        self._kernel = kernel or IntelligenceKernel(auto_init=True)
        self._agent_id = None
        self._agent_name = None

    # ── Lifecycle ────────────────────────────────────────────
    def adopt(self, agent_id, agent_name):
        self._agent_id = agent_id
        self._agent_name = agent_name
        return self

    def release(self):
        self._agent_id = None
        self._agent_name = None

    # ── Memory ───────────────────────────────────────────────
    def store(self, content, mem_type="semantic", importance=0.5):
        if not self._agent_id:
            return None
        return self._kernel.remember(self._agent_id, content, mem_type, importance)

    def recall(self, query, limit=10):
        return self._kernel.recall(query, limit)

    def store_episode(self, ep_type, content, data=None, outcome=None):
        if not self._agent_id:
            return None
        return self._kernel.store_episode(self._agent_id, ep_type, content, data, outcome)

    def add_concept(self, name, description, category="general"):
        return self._kernel.add_concept(name, description, category, self._agent_name or "sdk")

    def add_relation(self, source, target, rel_type="related", weight=0.5):
        return self._kernel.add_relation(source, target, rel_type, weight)

    def get_concepts(self, category=""):
        return self._kernel.get_concepts(category)

    def get_relations(self, source=""):
        return self._kernel.get_relations(source)

    # ── Communication ────────────────────────────────────────
    def send(self, recipient, content, msg_type="message", payload=None):
        if not self._agent_name:
            return False
        msg = self._kernel.bus.create_message(
            self._agent_name, msg_type, payload or {}, recipient
        )
        msg["content"] = content
        return self._kernel.bus.send(msg)

    def broadcast(self, msg_type, payload):
        return self._kernel.broadcast(msg_type, payload)

    def request(self, recipient, payload, timeout=5.0):
        if not self._agent_name:
            return None
        return self._kernel.request(self._agent_name, recipient, payload, timeout=timeout)

    def reply(self, original_msg, payload):
        return self._kernel.bus.reply(original_msg, payload)

    def discover_agents(self, capability=None, timeout=2.0):
        if not self._agent_name:
            return []
        return self._kernel.bus.discover_agents(self._agent_name, capability, timeout)

    # ── Identity ─────────────────────────────────────────────
    def create_identity(self, name, kind="agent", role="user", metadata=None):
        return self._kernel.create_identity(name, kind, role, metadata)

    def grant_permission(self, identity_id, resource, action):
        return self._kernel.grant_permission(identity_id, resource, action)

    def check_permission(self, identity_id, resource, action):
        return self._kernel.check_permission(identity_id, resource, action)

    def compute_trust(self, identity_id):
        return self._kernel.compute_trust(identity_id)

    # ── Oversight ────────────────────────────────────────────
    def request_approval(self, action, resource, context=None, risk_level="medium"):
        if not self._agent_name:
            return None
        return self._kernel.request_approval(self._agent_name, action, resource, context, risk_level)

    def get_pending_approvals(self):
        return self._kernel.get_pending_approvals()

    def approve(self, workflow_id, reason="Approved"):
        return self._kernel.approve(workflow_id, self._agent_name or "sdk", reason)

    def deny(self, workflow_id, reason="Denied"):
        return self._kernel.deny(workflow_id, self._agent_name or "sdk", reason)

    def explain(self, workflow_id):
        return self._kernel.explain(workflow_id)

    def search_audit(self, category="", limit=100):
        return self._kernel.search_audit(category, limit)

    # ── System ───────────────────────────────────────────────
    def status(self):
        return self._kernel.status()

    def spawn(self, name, role, capabilities=None, metadata=None):
        return self._kernel.spawn(name, role, capabilities, metadata)

    def delegate(self, name, task_type, payload, priority=5):
        return self._kernel.delegate(name, task_type, payload, priority)

    def agents_status(self):
        return self._kernel.agents_status()

    def get_message_history(self, msg_type="", limit=50):
        return self._kernel.get_message_history(msg_type, limit)

    def get_organizational_stats(self):
        return self._kernel.get_organizational_stats()

    @property
    def kernel(self):
        return self._kernel


class SystemSDK:
    def __init__(self, kernel=None):
        self._kernel = kernel or IntelligenceKernel(auto_init=True)

    def remember(self, content, importance=0.5):
        return self._kernel.remember("system", content, "semantic", importance)

    def recall(self, query, limit=10):
        return self._kernel.recall(query, limit)

    def add_concept(self, name, description, category="general"):
        return self._kernel.add_concept(name, description, category, "system")

    def add_relation(self, source, target, rel_type="related", weight=0.5):
        return self._kernel.add_relation(source, target, rel_type, weight)

    def get_concepts(self, category=""):
        return self._kernel.get_concepts(category)

    def get_relations(self, source=""):
        return self._kernel.get_relations(source)

    def get_organizational_stats(self):
        return self._kernel.get_organizational_stats()

    def broadcast(self, msg_type, payload):
        return self._kernel.broadcast(msg_type, payload)

    def get_message_history(self, msg_type="", limit=50):
        return self._kernel.get_message_history(msg_type, limit)

    def spawn(self, name, role, capabilities=None, metadata=None):
        return self._kernel.spawn(name, role, capabilities, metadata)

    def delegate(self, name, task_type, payload, priority=5):
        return self._kernel.delegate(name, task_type, payload, priority)

    def list_agents(self):
        return self._kernel.list_agents()

    def agents_status(self):
        return self._kernel.agents_status()

    def get_pending_approvals(self):
        return self._kernel.get_pending_approvals()

    def approve(self, workflow_id, approver, reason="Approved"):
        return self._kernel.approve(workflow_id, approver, reason)

    def deny(self, workflow_id, approver, reason="Denied"):
        return self._kernel.deny(workflow_id, approver, reason)

    def search_audit(self, category="", limit=100):
        return self._kernel.search_audit(category, limit)

    def create_identity(self, name, kind="user", role="admin", metadata=None):
        return self._kernel.create_identity(name, kind, role, metadata)

    def grant_permission(self, identity_id, resource, action):
        return self._kernel.grant_permission(identity_id, resource, action)

    def check_permission(self, identity_id, resource, action):
        return self._kernel.check_permission(identity_id, resource, action)

    def compute_trust(self, identity_id):
        return self._kernel.compute_trust(identity_id)

    def status(self):
        return self._kernel.status()

    @property
    def kernel(self):
        return self._kernel


class UserSDK:
    def __init__(self, kernel=None):
        self._kernel = kernel or IntelligenceKernel(auto_init=True)

    def recall(self, query, limit=10):
        return self._kernel.recall(query, limit)

    def get_concepts(self, category=""):
        return self._kernel.get_concepts(category)

    def get_relations(self, source=""):
        return self._kernel.get_relations(source)

    def get_organizational_stats(self):
        return self._kernel.get_organizational_stats()

    def status(self):
        return self._kernel.status()

    def list_agents(self):
        return self._kernel.list_agents()

    def agents_status(self):
        return self._kernel.agents_status()

    def get_pending_approvals(self):
        return self._kernel.get_pending_approvals()

    def get_message_history(self, msg_type="", limit=50):
        return self._kernel.get_message_history(msg_type, limit)

    def search_audit(self, category="", limit=100):
        return self._kernel.search_audit(category, limit)

    def explain(self, workflow_id):
        return self._kernel.explain(workflow_id)

    @property
    def kernel(self):
        return self._kernel
