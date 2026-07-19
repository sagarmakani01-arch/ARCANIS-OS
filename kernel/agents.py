import json
import threading
import time
import queue
import uuid
from datetime import datetime

from .memory import MemoryStore
from .identity import IdentityStore
from .communication import MessageBus


class AgentContext:
    def __init__(self, agent_id, name, capabilities, permissions, memory, identity, bus):
        self.agent_id = agent_id
        self.name = name
        self.capabilities = capabilities
        self.permissions = permissions
        self.memory = memory
        self.identity = identity
        self.bus = bus
        self.goals = []
        self.state = {}
        self.created = time.time()


class BaseAgent(threading.Thread):
    def __init__(self, context):
        super().__init__(daemon=True)
        self.ctx = context
        self._halt = threading.Event()
        self._mailbox = queue.Queue()
        self.status = "idle"

    def run(self):
        self.status = "active"
        self.ctx.bus.broadcast("kernel", MessageBus.AGENT_ACTIVATED, {
            "agent_id": self.ctx.agent_id, "name": self.ctx.name
        })
        while not self._halt.is_set():
            try:
                msg = self._mailbox.get(timeout=2)
                self._handle(msg)
            except queue.Empty:
                self._tick()
        self.status = "idle"
        self.ctx.bus.broadcast("kernel", MessageBus.AGENT_DEACTIVATED, {
            "agent_id": self.ctx.agent_id, "name": self.ctx.name
        })

    def send(self, message):
        self._mailbox.put(message)

    def stop(self):
        self._halt.set()

    def _handle(self, msg):
        msg_type = msg.get("type", "log")
        if msg_type == "task.delegate":
            self._handle_task(msg)
        elif msg_type == "request":
            self._handle_request(msg)
        elif msg_type == "command":
            self._handle_command(msg)
        elif msg_type == "message":
            self._handle_message(msg)
        else:
            self._log("info", f"Received: {msg_type}")

    def _handle_task(self, msg):
        task_type = msg.get("task_type", "general")
        payload = msg.get("payload", {})
        self._log("task", f"Processing task: {task_type}", payload)
        try:
            result = self._execute_task(task_type, payload)
            self.ctx.bus.delegate_result(msg, result)
            self.ctx.memory.store_episode(
                self.ctx.agent_id, "task", f"Completed {task_type}",
                {"task": task_type, "payload": payload, "result": str(result)[:200]},
                "success"
            )
        except Exception as e:
            self.ctx.bus.send(self.ctx.bus.create_message(
                self.ctx.agent_id, "task.failed", {"error": str(e)},
                recipient=msg.get("sender"),
                correlation_id=msg.get("correlation_id"),
            ))
            self._log("error", f"Task failed: {e}")

    def _handle_request(self, msg):
        payload = msg.get("payload", {})
        self._log("request", f"Request received: {payload.get('action', 'unknown')}")
        response = self._process_request(payload)
        self.ctx.bus.reply(msg, response)

    def _handle_command(self, msg):
        command = msg.get("content", "")
        payload = msg.get("payload", {})
        self._log("command", f"Command: {command}")
        self._execute_command(command, payload)

    def _handle_message(self, msg):
        self._log("info", f"Message: {msg.get('content', '')[:100]}")

    def _execute_task(self, task_type, payload):
        raise NotImplementedError

    def _process_request(self, payload):
        return {"status": "unhandled", "message": "No request handler"}

    def _execute_command(self, command, payload):
        pass

    def _tick(self):
        pass

    def _log(self, level, content, payload=None):
        self.ctx.memory.store_semantic(
            self.ctx.agent_id, f"[{level}] {content}",
            memory_type="log", importance=0.3
        )
        self.ctx.bus.broadcast(self.ctx.agent_id, MessageBus.AGENT_ACTIVITY, {
            "agent_id": self.ctx.agent_id,
            "name": self.ctx.name,
            "activity": content[:80],
        })


class ResearcherAgent(BaseAgent):
    def _execute_task(self, task_type, payload):
        if task_type == "research":
            topic = payload.get("topic", "unknown")
            depth = payload.get("depth", "basic")
            self._log("research", f"Researching: {topic} (depth={depth})")
            concepts = self.ctx.memory.get_concepts(topic)
            related = []
            if concepts:
                for c in concepts[:5]:
                    rels = self.ctx.memory.get_relations(c["name"])
                    related.extend(r["target_name"] for r in rels)
            knowledge = {
                "topic": topic,
                "direct_matches": len(concepts),
                "related_concepts": list(set(related))[:10],
            }
            self.ctx.memory.store_episode(
                self.ctx.agent_id, "research", f"Researched: {topic}", knowledge, "completed"
            )
            return knowledge
        elif task_type == "learn":
            topic = payload.get("topic", "")
            desc = payload.get("description", "")
            category = payload.get("category", "research")
            cid = self.ctx.memory.add_concept(topic, desc, category, self.ctx.agent_id)
            return {"concept_id": cid, "topic": topic}
        elif task_type == "explore":
            concepts = self.ctx.memory.get_concepts()
            relations_found = 0
            for c in concepts[:15]:
                rels = self.ctx.memory.get_relations(c["name"])
                if not rels:
                    for other in concepts[:15]:
                        if other["name"] != c["name"]:
                            self.ctx.memory.add_relation(c["name"], other["name"], "related", 0.3)
                            relations_found += 1
                            break
            return {"concepts_checked": min(len(concepts), 15), "relations_created": relations_found}
        return {"error": f"Unknown task: {task_type}"}

    def _tick(self):
        if time.time() % 30 < 0.5:
            concepts = self.ctx.memory.get_concepts()
            if concepts and len(concepts) > 1:
                import random
                topic = random.choice(concepts)["name"]
                rels = self.ctx.memory.get_relations(topic)
                if not rels:
                    others = [c for c in concepts if c["name"] != topic]
                    if others:
                        target = random.choice(others)["name"]
                        self.ctx.memory.add_relation(topic, target, "related", 0.5)
                        self._log("research", f"Auto-linked: {topic} -> {target}")


class AnalystAgent(BaseAgent):
    def _execute_task(self, task_type, payload):
        if task_type == "analyze":
            target = payload.get("target", "all")
            dimension = payload.get("dimension", "overview")
            if target == "concepts":
                concepts = self.ctx.memory.get_concepts()
                categories = {}
                for c in concepts:
                    cat = c.get("category", "general")
                    categories[cat] = categories.get(cat, 0) + 1
                return {"type": "concept_analysis", "total": len(concepts), "categories": categories}
            elif target == "relations":
                relations = self.ctx.memory.get_relations()
                types = {}
                for r in relations:
                    rt = r.get("relation_type", "related")
                    types[rt] = types.get(rt, 0) + 1
                return {"type": "relation_analysis", "total": len(relations), "types": types}
            elif target == "system":
                stats = self.ctx.memory.get_organizational_stats()
                return {"type": "system_analysis", "stats": stats}
            return {"type": "analysis", "target": target, "message": "Analysis complete"}
        elif task_type == "correlate":
            sources = payload.get("sources", [])
            if len(sources) >= 2:
                created = 0
                for i in range(len(sources)):
                    for j in range(i + 1, len(sources)):
                        self.ctx.memory.add_relation(sources[i], sources[j], "correlated", 0.7)
                        created += 1
                return {"correlations_created": created, "sources": sources}
            return {"error": "Need at least 2 sources"}
        return {"error": f"Unknown task: {task_type}"}

    def _tick(self):
        if time.time() % 45 < 0.5:
            concepts = self.ctx.memory.get_concepts(limit=15)
            if len(concepts) >= 3:
                import random
                pair = random.sample(concepts, 2)
                existing = self.ctx.memory.get_relations(pair[0]["name"])
                targets = {r["target_name"] for r in existing}
                if pair[1]["name"] not in targets:
                    self.ctx.memory.add_relation(pair[0]["name"], pair[1]["name"], "discovered", 0.4)
                    self._log("analysis", f"Discovered link: {pair[0]['name']} <-> {pair[1]['name']}")


class MonitorAgent(BaseAgent):
    def __init__(self, context):
        super().__init__(context)
        self._history = []

    def _execute_task(self, task_type, payload):
        if task_type == "status":
            memory_stats = self.ctx.memory.get_organizational_stats()
            return {"status": "operational", "memory": memory_stats, "agent_id": self.ctx.agent_id}
        elif task_type == "report":
            return self._generate_report()
        elif task_type == "watch":
            target = payload.get("target", "system")
            self._log("monitor", f"Watching: {target}")
            return {"watching": target}
        return {"error": f"Unknown task: {task_type}"}

    def _process_request(self, payload):
        action = payload.get("action", "status")
        if action == "health":
            return {"status": "healthy", "uptime": time.time() - self.ctx.created}
        return {"status": "unknown", "action": action}

    def _tick(self):
        if time.time() % 20 < 0.5:
            stats = self.ctx.memory.get_organizational_stats()
            self._history.append({"time": time.time(), "stats": stats})
            if len(self._history) > 100:
                self._history = self._history[-100:]

    def _generate_report(self):
        stats = self.ctx.memory.get_organizational_stats()
        concepts = self.ctx.memory.get_concepts()
        lines = [
            "=== ARCANIS Intelligence Report ===",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Generator: {self.ctx.name} ({self.ctx.agent_id[:8]})",
            "",
            "--- Memory Statistics ---",
            f"  Concepts: {stats['concepts']}",
            f"  Relations: {stats['relations']}",
            f"  Semantic Memories: {stats['semantic_memories']}",
            f"  Episodic Memories: {stats['episodic_memories']}",
            f"  Knowledge Versions: {stats['knowledge_versions']}",
            "",
            "--- Knowledge Overview ---",
        ]
        for c in concepts[:10]:
            rels = self.ctx.memory.get_relations(c["name"])
            lines.append(f"  - {c['name']} ({c['category']}): {len(rels)} relations")
        lines.extend(["", f"Report generated by {self.ctx.name}"])
        report = "\n".join(lines)
        self.ctx.memory.store_episode(
            self.ctx.agent_id, "report", "Generated system report",
            {"report_length": len(report)}, "completed"
        )
        return {"report": report, "stats": stats}


class AgentRuntime:
    def __init__(self):
        self.memory = MemoryStore()
        self.identity = IdentityStore()
        self.bus = MessageBus()
        self.agents = {}
        self._lock = threading.RLock()

    def create_agent(self, name, role, capabilities=None, metadata=None):
        with self._lock:
            ident = self.identity.create_identity(name, "agent", role, metadata)
            if not ident:
                return None
            self.identity.grant_permission(ident["id"], f"agent:{name}", "execute")
            self.identity.grant_permission(ident["id"], "memory:read", "read")
            self.identity.grant_permission(ident["id"], "memory:write", "write")
            self.identity.grant_permission(ident["id"], "bus:send", "send")

            context = AgentContext(
                agent_id=ident["id"],
                name=name,
                capabilities=capabilities or [role],
                permissions={"memory": True, "communication": True},
                memory=self.memory,
                identity=self.identity,
                bus=self.bus,
            )

            cls_map = {
                "research": ResearcherAgent,
                "analysis": AnalystAgent,
                "monitoring": MonitorAgent,
            }
            agent_cls = cls_map.get(role, BaseAgent)
            agent = agent_cls(context)
            self.agents[name] = agent
            agent.start()

            self.memory.store_episode("kernel", "agent.spawn",
                f"Agent '{name}' spawned with role '{role}'",
                {"agent_id": ident["id"], "role": role}, "success")
            return {"id": ident["id"], "name": name, "role": role}

    def get_agent(self, name):
        return self.agents.get(name)

    def send_to(self, name, message):
        with self._lock:
            agent = self.agents.get(name)
            if agent:
                agent.send(message)
                return True
            return False

    def delegate(self, name, task_type, payload, priority=5):
        agent = self.agents.get(name)
        if not agent:
            return None
        msg = self.bus.create_message(
            "kernel", "task.delegate", payload, name, priority=priority
        )
        msg["task_type"] = task_type
        agent.send(msg)
        return msg["id"]

    def broadcast(self, message):
        for agent in self.agents.values():
            agent.send(message)

    def get_status(self):
        return {name: agent.status for name, agent in self.agents.items()}

    def get_agent_info(self, name):
        agent = self.agents.get(name)
        if not agent:
            return None
        return {
            "name": agent.ctx.name,
            "id": agent.ctx.agent_id,
            "status": agent.status,
            "capabilities": agent.ctx.capabilities,
            "created": agent.ctx.created,
        }

    def list_agents(self):
        return [self.get_agent_info(name) for name in self.agents]

    def stop_all(self):
        for agent in self.agents.values():
            agent.stop()
        for agent in self.agents.values():
            agent.join(timeout=3)
        self.memory.store_episode("kernel", "system.shutdown",
            "All agents stopped", {"count": len(self.agents)}, "success")

    def get_stats(self):
        return {
            "agents": len(self.agents),
            "active": sum(1 for a in self.agents.values() if a.status == "active"),
            "memory": self.memory.get_organizational_stats(),
            "identity": self.identity.get_stats(),
            "communication": self.bus.get_stats(),
        }
