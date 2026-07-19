import json
import time
import threading
from datetime import datetime

from .memory import MemoryStore
from .identity import IdentityStore
from .communication import MessageBus
from .agents import AgentRuntime
from .oversight import OversightLayer


class IntelligenceKernel:
    def __init__(self, data_dir=None, auto_init=True):
        self.data_dir = data_dir
        self.started = time.time()
        self._stopped = threading.Event()

        # Core layers
        self.memory = MemoryStore(data_dir)
        self.identity = IdentityStore(data_dir)
        self.bus = MessageBus()
        self.agents = AgentRuntime()

        # Oversight (depends on bus)
        self.oversight = OversightLayer(self.bus)

        # Layer registry for SDK access
        self._layers = {
            "memory": self.memory,
            "identity": self.identity,
            "communication": self.bus,
            "agents": self.agents,
            "oversight": self.oversight,
        }

        if auto_init:
            self._initialize()

    def _initialize(self):
        self.memory.store_episode("kernel", "system.boot", "ARCANIS kernel boot",
            {"version": "2.0.0", "timestamp": time.time()}, "success")
        self.bus.broadcast("kernel", MessageBus.SYSTEM_EVENT, {
            "event": "kernel.boot", "version": "2.0.0"
        })

    def layer(self, name):
        return self._layers.get(name)

    # ── Lifecycle ────────────────────────────────────────────
    def start(self):
        self.memory.store_episode("kernel", "system.start",
            "ARCANIS kernel started", {"timestamp": time.time()}, "success")
        self.bus.broadcast("kernel", MessageBus.SYSTEM_EVENT, {
            "event": "kernel.start", "timestamp": time.time()
        })

    def stop(self):
        self._stopped.set()
        self.agents.stop_all()
        self.memory.close()
        self.bus.broadcast("kernel", MessageBus.SYSTEM_EVENT, {
            "event": "kernel.stop", "uptime": time.time() - self.started
        })

    def restart(self):
        self.stop()
        self.memory = MemoryStore(self.data_dir)
        self.identity = IdentityStore(self.data_dir)
        self.bus = MessageBus()
        self.agents = AgentRuntime()
        self.oversight = OversightLayer(self.bus)
        self._layers = {
            "memory": self.memory, "identity": self.identity,
            "communication": self.bus, "agents": self.agents, "oversight": self.oversight,
        }
        self._initialize()
        self.start()

    # ── Agent Management ─────────────────────────────────────
    def spawn(self, name, role, capabilities=None, metadata=None):
        return self.agents.create_agent(name, role, capabilities, metadata)

    def send(self, name, content, msg_type="message", payload=None):
        msg = self.bus.create_message("kernel", msg_type, payload or {}, name)
        msg["content"] = content
        return self.agents.send_to(name, msg)

    def delegate(self, name, task_type, payload, priority=5):
        return self.agents.delegate(name, task_type, payload, priority)

    def agents_status(self):
        return self.agents.get_status()

    def agent_info(self, name):
        return self.agents.get_agent_info(name)

    def list_agents(self):
        return self.agents.list_agents()

    # ── Memory Actions ───────────────────────────────────────
    def remember(self, agent_id, content, mem_type="semantic", importance=0.5):
        return self.memory.store_semantic(agent_id, content, memory_type=mem_type, importance=importance)

    def recall(self, query, limit=10):
        return self.memory.search(query, limit=limit)

    def store_episode(self, agent_id, ep_type, content, data=None, outcome=None):
        return self.memory.store_episode(agent_id, ep_type, content, data or {}, outcome)

    def add_concept(self, name, description, category="general", source="kernel"):
        return self.memory.add_concept(name, description, category, source)

    def add_relation(self, source, target, rel_type="related", weight=0.5):
        return self.memory.add_relation(source, target, rel_type, weight)

    def get_concepts(self, category=""):
        return self.memory.get_concepts(category=category) if category else self.memory.get_concepts()

    def get_relations(self, source=""):
        return self.memory.get_relations(source) if source else self.memory.get_relations()

    def get_organizational_stats(self):
        return self.memory.get_organizational_stats()

    # ── Identity Actions ─────────────────────────────────────
    def create_identity(self, name, kind="agent", role="user", metadata=None):
        return self.identity.create_identity(name, kind, role, metadata)

    def verify_identity(self, identity_id, challenge):
        return self.identity.verify_identity(identity_id, challenge)

    def grant_permission(self, identity_id, resource, action):
        return self.identity.grant_permission(identity_id, resource, action)

    def check_permission(self, identity_id, resource, action):
        return self.identity.check_permission(identity_id, resource, action)

    def compute_trust(self, identity_id):
        return self.identity.compute_trust_score(identity_id)

    def get_audit_log(self, identity_id=""):
        return self.identity.get_audit_log(identity_id) if identity_id else self.identity.get_audit_log()

    # ── Communication Actions ────────────────────────────────
    def broadcast(self, msg_type, payload):
        self.bus.broadcast("kernel", msg_type, payload)

    def request(self, sender, recipient, payload, msg_type="request", timeout=5.0):
        return self.bus.request(sender, recipient, payload, msg_type, timeout)

    def get_message_history(self, msg_type="", limit=50):
        return self.bus.get_history(msg_type, limit)

    # ── Oversight Actions ────────────────────────────────────
    def request_approval(self, requester, action, resource, context=None, risk_level="medium"):
        return self.oversight.request_approval(requester, action, resource, context, risk_level)

    def approve(self, workflow_id, approver, reason="Approved"):
        return self.oversight.approve(workflow_id, approver, reason)

    def deny(self, workflow_id, approver, reason="Denied"):
        return self.oversight.deny(workflow_id, approver, reason)

    def get_pending_approvals(self):
        return self.oversight.get_pending_approvals()

    def explain(self, workflow_id):
        return self.oversight.explain(workflow_id)

    def rollback(self, workflow_id, actor):
        return self.oversight.rollback(workflow_id, actor)

    def search_audit(self, category="", limit=100):
        return self.oversight.search_audit(category, limit)

    # ── Query / Stats ────────────────────────────────────────
    def status(self):
        uptime = time.time() - self.started
        agents = self.agents_status()
        memory_stats = self.memory.get_organizational_stats()
        identity_stats = self.identity.get_stats()
        bus_stats = self.bus.get_stats()
        oversight_stats = self.oversight.get_stats()

        return {
            "status": "running" if not self._stopped.is_set() else "stopped",
            "uptime": uptime,
            "uptime_human": f"{uptime / 3600:.1f}h" if uptime > 3600 else f"{uptime / 60:.1f}m",
            "kernel_version": "2.0.0",
            "agents": {"total": len(agents), "active": sum(1 for s in agents.values() if s == "active")},
            "memory": memory_stats,
            "identity": identity_stats,
            "communication": bus_stats,
            "oversight": oversight_stats,
        }
