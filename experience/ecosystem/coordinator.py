import json
import threading
import os
from datetime import datetime
from .database import Database
from .knowledge import KnowledgeEngine
from .projects import ProjectManager
from .agents import AgentSystem
from .tasks import TaskEngine


class EcosystemCoordinator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db = Database()
        self.knowledge = KnowledgeEngine()
        self.projects = ProjectManager()
        self.agents = AgentSystem(self.knowledge, self.projects)
        self.tasks = TaskEngine(self.db)
        self._seed_data()

    def _seed_data(self):
        c = self.db.get_concept_count()
        if c > 0:
            return

        concepts = [
            ("ARCANIS", "Enterprise ecosystem platform", "system"),
            ("Multi-Agent System", "Coordinated AI agents working together", "ai"),
            ("Knowledge Graph", "Network of concepts and their relationships", "ai"),
            ("Neural Networks", "Computing systems inspired by biological neural networks", "ai"),
            ("Natural Language Processing", "AI understanding and generating human language", "ai"),
            ("Reinforcement Learning", "Learning through trial and error with rewards", "ai"),
            ("Vector Embeddings", "Numerical representations of concepts", "ai"),
            ("Task Orchestration", "Coordinating and managing task execution", "system"),
            ("Real-time Monitoring", "Continuous observation of system state", "system"),
            ("Project Lifecycle", "Phases of project from inception to completion", "system"),
            ("Memory Persistence", "Storing and recalling information over time", "system"),
            ("Agent Communication", "Message passing between autonomous agents", "ai"),
        ]
        for name, desc, cat in concepts:
            self.db.add_concept(name, desc, cat)

        relations = [
            ("ARCANIS", "Multi-Agent System", "contains"),
            ("ARCANIS", "Knowledge Graph", "contains"),
            ("ARCANIS", "Task Orchestration", "contains"),
            ("ARCANIS", "Real-time Monitoring", "contains"),
            ("ARCANIS", "Memory Persistence", "contains"),
            ("Multi-Agent System", "Agent Communication", "uses"),
            ("Multi-Agent System", "Task Orchestration", "uses"),
            ("Knowledge Graph", "Vector Embeddings", "uses"),
            ("Neural Networks", "Natural Language Processing", "enables"),
            ("Neural Networks", "Reinforcement Learning", "enables"),
            ("Natural Language Processing", "Agent Communication", "enables"),
            ("Task Orchestration", "Project Lifecycle", "manages"),
        ]
        for s, t, r in relations:
            self.db.add_relation(s, t, r)

        self.db.add_memory("Ecosystem initialized with seed data", "system", "initialization")

        self.projects.create("Ecosystem Architecture", "Core architecture design for ARCANIS ecosystem", "high")
        self.projects.create("Agent Framework", "Multi-agent coordination framework", "high")
        self.projects.create("Knowledge Base", "Persistent knowledge storage and retrieval", "medium")

        for proj in self.db.get_projects():
            pid = proj["id"]
            self.db.add_task(pid, f"Define requirements for {proj['name']}", "Initial planning phase", "high")
            self.db.add_task(pid, f"Implement core {proj['name']}", "Main implementation", "medium")
            self.db.add_task(pid, f"Test and validate {proj['name']}", "Quality assurance", "medium")

    def get_stats(self):
        return self.db.get_stats()

    def get_concepts(self, search=""):
        return self.db.get_concepts(search)

    def get_memories(self, limit=50):
        return self.db.get_memories(limit)

    def get_agent_status(self):
        return self.agents.get_status()

    def get_agent_messages(self, limit=30):
        return self.agents.get_messages(limit)

    def get_projects(self):
        return self.db.get_projects()

    def get_tasks(self, project_id=-1):
        return self.db.get_tasks(project_id)

    def command(self, text):
        parts = text.strip().split()
        if not parts:
            return "No command"
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("learn", "teach"):
            concept = " ".join(args)
            if concept:
                self.knowledge.learn(concept)
                return f"\u2713 Learned: {concept}"
            return "Usage: learn <concept>"

        elif cmd == "relate":
            if len(args) >= 2:
                source = args[0]
                target = args[1]
                rel = args[2] if len(args) > 2 else "related"
                self.knowledge.relate(source, target, rel)
                return f"\u2713 Related '{source}' \u2192 '{target}' ({rel})"
            return "Usage: relate <source> <target> [type]"

        elif cmd == "search":
            q = " ".join(args)
            if not q:
                return "Usage: search <query>\nAll concepts:\n" + "\n".join(f"  - {c['name']}" for c in self.get_concepts()[:20])
            results = self.knowledge.search(q)
            if results:
                return f"Found {len(results)}:\n" + "\n".join(f"  - {c['name']}: {c['description'][:50]}" for c in results[:10])
            return "No results"

        elif cmd == "stats":
            s = self.get_stats()
            return (f"Concepts: {s['concepts']}  |  Relations: {s['relations']}  |  "
                    f"Memories: {s['memories']}  |  Projects: {s['projects']}  |  "
                    f"Tasks: {s['tasks']}  |  Agents: {s['agents']} ({s['agents_active']} active)")

        elif cmd == "projects":
            projects = self.get_projects()
            if not projects:
                return "No projects"
            lines = [f"  {p['name']} ({p['status']})" for p in projects]
            return "Projects:\n" + "\n".join(lines)

        elif cmd == "agents":
            status = self.get_agent_status()
            agents = self.db.get_agents()
            if not agents:
                return "No agents"
            lines = [f"  {a['name']}: {status.get(a['name'], 'idle')} ({a['role']})" for a in agents]
            return "Agents:\n" + "\n".join(lines)

        elif cmd == "create":
            name = " ".join(args)
            if name:
                pid = self.projects.create(name)
                return f"\u2713 Created project: {name} (id={pid})"
            return "Usage: create <project name>"

        elif cmd == "help":
            return ("\u2716 Commands:\n"
                    "  learn <c>     \u2014 Learn a new concept\n"
                    "  relate a b    \u2014 Relate two concepts\n"
                    "  search <q>    \u2014 Search knowledge base\n"
                    "  stats         \u2014 Ecosystem statistics\n"
                    "  projects      \u2014 List projects\n"
                    "  agents        \u2014 List agents\n"
                    "  tasks         \u2014 Project tasks\n"
                    "  create <n>    \u2014 Create project\n"
                    "  memories      \u2014 Show recent memories\n"
                    "  generate <t> <n> \u2014 Generate file (script,html,markdown)\n"
                    "  code read/write \u2014 Read/write files\n"
                    "  research <t>  \u2014 Research a topic\n"
                    "  run <cmd>     \u2014 Run system command\n"
                    "  system info   \u2014 System information\n"
                    "  open <file>   \u2014 Open file/app\n"
                    "  task status   \u2014 Task queue status")

        elif cmd == "memories":
            mems = self.get_memories(10)
            if not mems:
                return "No memories"
            lines = [f"[{m['level']}] {m['content'][:60]}" for m in mems]
            return "Recent memories:\n" + "\n".join(f"  {l}" for l in lines)

        elif cmd == "tasks":
            projects = self.get_projects()
            if not projects:
                return "No projects"
            lines = []
            for p in projects[:3]:
                tasks = self.get_tasks(p["id"])
                done = sum(1 for t in tasks if t["status"] == "completed")
                lines.append(f"{p['name']}: {done}/{len(tasks)} done")
                for t in tasks[:3]:
                    lines.append(f"  [{t['status']}] {t['title']}")
            return "\n".join(lines)

        elif cmd in ("run", "execute"):
            full = " ".join(args)
            if full:
                try:
                    import subprocess, sys
                    result = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=10)
                    out = result.stdout.strip()[:200] or result.stderr.strip()[:200] or "Done"
                    return f"$ {full}\n{out}"
                except Exception as e:
                    return f"Error: {e}"
            return "Usage: run <command>"

        elif cmd == "open":
            full = " ".join(args)
            if full:
                try:
                    import subprocess
                    subprocess.Popen(full, shell=True)
                    return f"\u2713 Opened: {full}"
                except Exception as e:
                    return f"Error: {e}"
            return "Usage: open <file or app>"

        elif cmd == "generate":
            parts2 = text.strip().split(None, 2)
            if len(parts2) >= 2:
                template = parts2[1] if len(parts2) > 1 else "script"
                name = parts2[2] if len(parts2) > 2 else "untitled"
                gen_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".ecosystem", "generated")
                os.makedirs(gen_dir, exist_ok=True)
                tid = self.tasks.submit(f"Generate {name}", "code", {
                    "action": "generate", "template": template, "name": name, "path": os.path.join(gen_dir, name)
                })
                return f"\u23F3 Generating {template} '{name}' (task #{tid})"
            return "Usage: generate <script|html|markdown> <name>"

        elif cmd == "task":
            action = args[0] if args else "status"
            if action == "status":
                pending = self.tasks.get_pending_count()
                results = self.tasks.get_results()
                recent = [f"  #{r.id} {r.name}: {r.status}" for r in results[-5:]]
                return f"Pending: {pending}\nRecent:\n" + "\n".join(recent) if recent else f"Pending: {pending}\nNo completed tasks"

        elif cmd == "code":
            action = args[0] if args else "help"
            if action == "read" and len(args) >= 2:
                tid = self.tasks.submit(f"Read {args[1]}", "code", {"action": "read", "path": args[1]})
                return f"\u23F3 Reading {args[1]} (task #{tid})"
            elif action == "write" and len(args) >= 3:
                path = args[1]
                content = " ".join(args[2:])
                tid = self.tasks.submit(f"Write {path}", "code", {"action": "write", "path": path, "content": content})
                return f"\u23F3 Writing to {path} (task #{tid})"
            return "Usage: code read <path> | code write <path> <content>"

        elif cmd == "research":
            topic = " ".join(args)
            if topic:
                tid = self.tasks.submit(f"Research {topic}", "research", {"action": "learn", "topic": topic})
                return f"\u23F3 Researching: {topic} (task #{tid})"
            return "Usage: research <topic>"

        elif cmd == "system":
            action = args[0] if args else "info"
            if action == "info":
                tid = self.tasks.submit("System info", "system", {"action": "info"})
            elif action == "run" and len(args) >= 2:
                cmd2 = " ".join(args[1:])
                tid = self.tasks.submit(f"Run {cmd2}", "system", {"action": "run", "command": cmd2})
            else:
                return "Usage: system info | system run <command>"
            return f"\u23F3 System {action} (task #{tid})"

        else:
            return f"Unknown: '{cmd}'. Type 'help' for commands."
