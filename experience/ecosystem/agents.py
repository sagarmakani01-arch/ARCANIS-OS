import json
import threading
import time
import queue
import random
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
        self.db.add_agent_message(self.agent_id, msg.get("type", "log"),
                                  msg.get("content", ""), msg.get("payload"))

    def _tick(self):
        pass


class ResearcherAgent(BaseAgent):
    def _tick(self):
        if random.random() < 0.15:
            topics = ["neural networks", "knowledge graphs", "multi-agent systems",
                      "natural language processing", "computer vision",
                      "reinforcement learning", "distributed systems"]
            topic = random.choice(topics)
            self.db.add_agent_message(self.agent_id, "research",
                                      f"Analyzing {topic}", {"topic": topic})
            self.knowledge.learn(topic, f"Research topic: {topic}", "research")
            self.db.add_memory(f"Researcher: analyzed {topic}", "agent", "research")


class AnalystAgent(BaseAgent):
    def _tick(self):
        if random.random() < 0.1:
            concepts = self.db.get_concepts(limit=5)
            if len(concepts) >= 2:
                pair = random.sample(concepts, 2)
                gap = f"{pair[0]['name']} vs {pair[1]['name']}"
                self.db.add_agent_message(self.agent_id, "analysis",
                                          f"Analyzing relationship gap: {gap}",
                                          {"source": pair[0]["name"], "target": pair[1]["name"]})
                self.knowledge.relate(pair[0]["name"], pair[1]["name"], "related", 0.5)


class MonitorAgent(BaseAgent):
    def _tick(self):
        if random.random() < 0.08:
            stats = self.db.get_stats()
            self.db.add_agent_message(self.agent_id, "monitor",
                                      f"System stats: {stats['concepts']} concepts, {stats['projects']} projects",
                                      stats)
            self.db.set_state("last_stats", json.dumps(stats))


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
