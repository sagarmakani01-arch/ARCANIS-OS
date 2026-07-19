import json
import threading
import time
import queue
import random
import os
from datetime import datetime
from .database import Database


class BaseAgent(threading.Thread):
    def __init__(self, agent_id, name, role, db, knowledge, projects):
        super().__init__(daemon=True)
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.db = db
        self.knowledge = knowledge
        self.projects = projects
        self._stop = threading.Event()
        self._mailbox = queue.Queue()
        self.status = "idle"

    def run(self):
        self.db.update_agent_status(self.agent_id, "active")
        self.status = "active"
        while not self._stop.is_set():
            try:
                msg = self._mailbox.get(timeout=2)
                self._process_message(msg)
            except queue.Empty:
                self._tick()
        self.db.update_agent_status(self.agent_id, "idle")
        self.status = "idle"

    def send(self, msg):
        self._mailbox.put(msg)

    def stop(self):
        self._stop.set()

    def _process_message(self, msg):
        msg_type = msg.get("type", "log")
        content = msg.get("content", "")
        payload = msg.get("payload", {})
        self.db.add_agent_message(self.agent_id, msg_type, content, payload)

        if msg_type == "command":
            self._handle_command(content, payload)

    def _handle_command(self, command, payload):
        self.db.add_memory(f"{self.name}: processing command '{command}'", "agent")

    def _tick(self):
        pass

    def _log(self, kind, content, payload=None):
        self.db.add_agent_message(self.agent_id, kind, content, payload)


class ResearcherAgent(BaseAgent):
    def _handle_command(self, command, payload):
        if command == "research":
            topic = payload.get("topic", "unknown")
            self._log("research", f"Researching: {topic}")
            self.db.add_memory(f"Researcher: researching '{topic}'", "agent", "research")
            concepts = self.db.get_concepts(topic)
            if not concepts:
                self.knowledge.learn(topic, f"Research topic requested by user", "research")
                self._log("research", f"Learned new concept: {topic}")
            else:
                related = []
                for c in concepts[:5]:
                    rels = self.db.get_relations(c["name"])
                    related.extend(r["target_name"] for r in rels)
                if related:
                    self._log("research", f"Found {len(related)} related concepts for '{topic}'")
                self._log("research", f"Analysis complete for: {topic}")

        elif command == "learn":
            topic = payload.get("topic", "unknown")
            desc = payload.get("description", "")
            category = payload.get("category", "research")
            self.knowledge.learn(topic, desc, category)
            self._log("research", f"Learned: {topic} ({category})")

        elif command == "explore":
            self._log("research", "Exploring knowledge graph for gaps")
            concepts = self.db.get_concepts()
            if len(concepts) >= 2:
                pairs_checked = 0
                relations_found = 0
                for c in concepts[:10]:
                    rels = self.db.get_relations(c["name"])
                    if not rels:
                        for other in concepts[:10]:
                            if other["name"] != c["name"]:
                                self.knowledge.relate(c["name"], other["name"], "related", 0.3)
                                relations_found += 1
                                break
                    pairs_checked += 1
                self._log("research", f"Exploration: checked {pairs_checked}, suggested {relations_found} new relations")

    def _tick(self):
        if random.random() < 0.1:
            concepts = self.db.get_concepts()
            if concepts:
                topic = random.choice(concepts)["name"]
                self._log("research", f"Autonomous analysis: {topic}")
                rels = self.db.get_relations(topic)
                if not rels:
                    others = [c for c in concepts if c["name"] != topic]
                    if others:
                        target = random.choice(others)["name"]
                        self.knowledge.relate(topic, target, "related", 0.5)
                        self._log("research", f"Created relation: {topic} -> {target}")


class AnalystAgent(BaseAgent):
    def _handle_command(self, command, payload):
        if command == "analyze":
            target = payload.get("target", "all")
            self._log("analysis", f"Analyzing: {target}")

            if target == "concepts":
                concepts = self.db.get_concepts()
                categories = {}
                for c in concepts:
                    cat = c.get("category", "general")
                    categories[cat] = categories.get(cat, 0) + 1
                summary = ", ".join(f"{k}: {v}" for k, v in categories.items())
                self._log("analysis", f"Concept analysis: {summary}")

            elif target == "relations":
                relations = self.db.get_relations()
                types = {}
                for r in relations:
                    rt = r.get("relation_type", "related")
                    types[rt] = types.get(rt, 0) + 1
                summary = ", ".join(f"{k}: {v}" for k, v in types.items())
                self._log("analysis", f"Relation analysis: {summary}")

            elif target == "projects":
                projects = self.db.get_projects()
                statuses = {}
                for p in projects:
                    s = p.get("status", "active")
                    statuses[s] = statuses.get(s, 0) + 1
                summary = ", ".join(f"{k}: {v}" for k, v in statuses.items())
                self._log("analysis", f"Project analysis: {summary}")
                for p in projects[:3]:
                    tasks = self.db.get_tasks(p["id"])
                    done = sum(1 for t in tasks if t["status"] == "completed")
                    self._log("analysis", f"  {p['name']}: {done}/{len(tasks)} tasks done")

            self._log("analysis", f"Analysis complete: {target}")

        elif command == "correlate":
            source = payload.get("source", "")
            target = payload.get("target", "")
            if source and target:
                self.knowledge.relate(source, target, "correlated", 0.8)
                self._log("analysis", f"Correlated: {source} <-> {target}")

    def _tick(self):
        if random.random() < 0.08:
            concepts = self.db.get_concepts(limit=10)
            if len(concepts) >= 3:
                pair = random.sample(concepts, 2)
                existing = self.db.get_relations(pair[0]["name"])
                existing_targets = {r["target_name"] for r in existing}
                if pair[1]["name"] not in existing_targets:
                    self.knowledge.relate(pair[0]["name"], pair[1]["name"], "related", 0.4)
                    self._log("analysis", f"Auto-correlated: {pair[0]['name']} -> {pair[1]['name']}")
                    self.db.add_memory(f"Analyst: linked {pair[0]['name']} to {pair[1]['name']}", "agent", "analysis")


class MonitorAgent(BaseAgent):
    def _handle_command(self, command, payload):
        if command == "status":
            stats = self.db.get_stats()
            import psutil
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                self._log("monitor", f"CPU: {cpu}% | MEM: {mem.percent}% | DISK: {disk.percent}%")
                self._log("monitor", f"Ecosystem: {stats['concepts']} concepts, {stats['projects']} projects, {stats['agents']} agents")
            except Exception:
                self._log("monitor", f"Ecosystem: {stats['concepts']} concepts, {stats['projects']} projects")

        elif command == "report":
            self._generate_report()

        elif command == "watch":
            target = payload.get("target", "system")
            self._log("monitor", f"Now watching: {target}")

    def _tick(self):
        if random.random() < 0.06:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.05)
                mem = psutil.virtual_memory()
                if cpu > 80:
                    self._log("monitor", f"High CPU alert: {cpu}%")
                if mem.percent > 85:
                    self._log("monitor", f"High memory alert: {mem.percent}%")
            except Exception:
                pass

    def _generate_report(self):
        stats = self.db.get_stats()
        concepts = self.db.get_concepts()
        projects = self.db.get_projects()
        lines = [
            f"=== ARCANIS System Report ===",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"Knowledge Base:",
            f"  Concepts: {stats['concepts']}",
            f"  Relations: {stats['relations']}",
            f"  Memories: {stats['memories']}",
            f"",
            f"Projects: {stats['projects']} ({stats['tasks_pending']} pending tasks)",
        ]
        for p in projects[:5]:
            tasks = self.db.get_tasks(p["id"])
            done = sum(1 for t in tasks if t["status"] == "completed")
            lines.append(f"  - {p['name']}: {done}/{len(tasks)} done")
        lines.append(f"")
        lines.append(f"Agents: {stats['agents']} ({stats['agents_active']} active)")

        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            lines.append(f"System: CPU {cpu}%, Memory {mem.percent}%")
        except Exception:
            pass

        report = "\n".join(lines)
        self._log("monitor", report[:200])
        self.db.set_state("last_report", report)
        self.db.add_memory(f"Monitor: generated system report", "agent", "monitor")


class AgentSystem:
    def __init__(self, knowledge, projects):
        self.db = Database()
        self.knowledge = knowledge
        self.projects = projects
        self.agents = {}
        self._ensure_default_agents()

    def _ensure_default_agents(self):
        defaults = [
            ("Researcher", "research", ["analysis", "research", "learning"]),
            ("Analyst", "analysis", ["data-analysis", "pattern-recognition"]),
            ("Monitor", "monitoring", ["monitoring", "reporting"]),
        ]
        for name, role, caps in defaults:
            agent_id = self.db.add_agent(name, role, caps)
            if agent_id:
                self._spawn(agent_id, name, role)

    def _spawn(self, agent_id, name, role):
        cls_map = {"research": ResearcherAgent, "analysis": AnalystAgent, "monitoring": MonitorAgent}
        cls = cls_map.get(role, BaseAgent)
        agent = cls(agent_id, name, role, self.db, self.knowledge, self.projects)
        self.agents[name] = agent
        agent.start()
        self.db.add_memory(f"Agent '{name}' ({role}) started", "agents")

    def send_to(self, name, msg):
        if name in self.agents:
            self.agents[name].send(msg)
            return True
        return False

    def broadcast(self, msg):
        for agent in self.agents.values():
            agent.send(msg)

    def get_status(self):
        return {name: agent.status for name, agent in self.agents.items()}

    def get_messages(self, limit=50):
        return self.db.get_agent_messages(limit=limit)

    def stop_all(self):
        for agent in self.agents.values():
            agent.stop()
        for agent in self.agents.values():
            agent.join(timeout=3)
        self.db.add_memory("All agents stopped", "agents")
