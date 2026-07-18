import threading
import queue
import time
import json
import subprocess
import os
from datetime import datetime
from .database import Database


class Task:
    def __init__(self, task_id, name, agent_type, payload, priority=5):
        self.id = task_id
        self.name = name
        self.agent_type = agent_type
        self.payload = payload
        self.priority = priority
        self.status = "pending"
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None


class BaseWorker(threading.Thread):
    def __init__(self, name, db, task_queue, result_queue):
        super().__init__(daemon=True)
        self.name = name
        self.db = db
        self.task_queue = task_queue
        self.result_queue = result_queue
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            try:
                task = self.task_queue.get(timeout=1)
                self._execute(task)
            except queue.Empty:
                continue

    def _execute(self, task):
        task.status = "running"
        task.started_at = datetime.now()
        self.db.add_agent_message(0, "task", f"{self.name} starting: {task.name}")
        try:
            result = self._process(task)
            task.status = "completed"
            task.result = result
            self.db.add_agent_message(0, "task", f"{self.name} completed: {task.name}", {"result": str(result)[:100]})
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.db.add_agent_message(0, "error", f"{self.name} failed: {task.name}: {e}")
        task.completed_at = datetime.now()
        self.result_queue.put(task)

    def _process(self, task):
        raise NotImplementedError

    def stop(self):
        self._stop.set()


class CodeWorker(BaseWorker):
    def _process(self, task):
        action = task.payload.get("action", "read")
        path = task.payload.get("path", "")
        content = task.payload.get("content", "")

        if action == "read":
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read()[:1000]
            return f"File not found: {path}"

        elif action == "write":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            self.db.add_memory(f"Wrote file: {path}", "code")
            return f"Written: {path} ({len(content)} chars)"

        elif action == "list":
            root = task.payload.get("root", ".")
            entries = []
            for e in os.listdir(root):
                full = os.path.join(root, e)
                entries.append(f"{'D' if os.path.isdir(full) else 'F'} {e}")
            return "\n".join(entries[:50])

        elif action == "generate":
            template = task.payload.get("template", "script")
            name = task.payload.get("name", "untitled")
            ext_map = {"script": ".py", "html": ".html", "markdown": ".md", "text": ".txt"}
            ext = ext_map.get(template, ".txt")
            filepath = task.payload.get("path", f"generated/{name}{ext}")
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            boilerplate = {
                "script": f"#!/usr/bin/env python3\n# {name}\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
                "html": f"<!DOCTYPE html>\n<html>\n<head><title>{name}</title></head>\n<body>\n</body>\n</html>\n",
                "markdown": f"# {name}\n\n",
            }
            write_content = boilerplate.get(template, content or f"# {name}\n")
            with open(filepath, "w") as f:
                f.write(write_content)
            self.db.add_memory(f"Generated {template}: {filepath}", "code")
            return f"Generated: {filepath}"

        return f"Unknown action: {action}"


class ResearchWorker(BaseWorker):
    def _process(self, task):
        action = task.payload.get("action", "search")
        query = task.payload.get("query", "")

        if action == "search":
            from ..ecosystem import EcosystemCoordinator
            eco = EcosystemCoordinator()
            results = eco.get_concepts(query)
            if results:
                lines = [f"{c['name']}: {c['description'][:80]}" for c in results[:10]]
                return "Found:\n" + "\n".join(lines)
            return f"No results for: {query}"

        elif action == "learn":
            topic = task.payload.get("topic", query)
            if topic:
                from ..ecosystem import EcosystemCoordinator
                eco = EcosystemCoordinator()
                eco.knowledge.learn(topic, f"Researched topic: {topic}", "research")
                return f"Learned: {topic}"
            return "No topic specified"

        elif action == "analyze":
            from ..ecosystem import EcosystemCoordinator
            eco = EcosystemCoordinator()
            stats = eco.get_stats()
            return json.dumps(stats, indent=2)

        return f"Unknown action: {action}"


class SystemWorker(BaseWorker):
    def _process(self, task):
        action = task.payload.get("action", "run")
        command = task.payload.get("command", "")

        if action == "run":
            if not command:
                return "No command"
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                out = result.stdout.strip()[:500] or result.stderr.strip()[:200] or "Done"
                return f"$ {command}\n{out}"
            except subprocess.TimeoutExpired:
                return "Command timed out"
            except Exception as e:
                return f"Error: {e}"

        elif action == "info":
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                return (f"CPU: {cpu}% | Memory: {mem.percent}% "
                        f"({mem.used//(1024**3)}GB/{mem.total//(1024**3)}GB) | "
                        f"Disk: {disk.percent}%")
            except ImportError:
                return "psutil not available"

        elif action == "processes":
            try:
                import psutil
                procs = sorted(psutil.process_iter(["pid", "name", "cpu_percent"]),
                              key=lambda p: p.info["cpu_percent"] or 0, reverse=True)[:10]
                return "\n".join(f"{p.info['pid']:6d} {p.info['cpu_percent']:5.1f}% {p.info['name'][:30]}" for p in procs)
            except ImportError:
                return "psutil not available"

        return f"Unknown action: {action}"


class ProjectWorker(BaseWorker):
    def _process(self, task):
        action = task.payload.get("action", "list")
        from ..ecosystem import EcosystemCoordinator
        eco = EcosystemCoordinator()

        if action == "list":
            projects = eco.get_projects()
            if not projects:
                return "No projects"
            return "\n".join(f"{p['name']} ({p['status']})" for p in projects)

        elif action == "create":
            name = task.payload.get("name", "")
            if name:
                pid = eco.projects.create(name, task.payload.get("description", ""))
                return f"Created: {name} (id={pid})"
            return "No name specified"

        elif action == "add_task":
            pid = task.payload.get("project_id")
            title = task.payload.get("title", "")
            if pid and title:
                tid = eco.projects.add_task(pid, title)
                return f"Added task: {title}"
            return "project_id and title required"

        elif action == "status":
            projects = eco.get_projects()
            lines = []
            for p in projects:
                tasks = eco.get_tasks(p["id"])
                done = sum(1 for t in tasks if t["status"] == "completed")
                total = len(tasks)
                lines.append(f"{p['name']}: {done}/{total} tasks done")
            return "\n".join(lines)

        return f"Unknown action: {action}"


class TaskEngine:
    def __init__(self, db=None):
        self.db = db or Database()
        self.task_queue = queue.PriorityQueue()
        self.result_queue = queue.Queue()
        self._task_counter = 0
        self._lock = threading.Lock()

        self.workers = {
            "code": CodeWorker("CodeWorker", self.db, self.task_queue, self.result_queue),
            "research": ResearchWorker("ResearchWorker", self.db, self.task_queue, self.result_queue),
            "system": SystemWorker("SystemWorker", self.db, self.task_queue, self.result_queue),
            "project": ProjectWorker("ProjectWorker", self.db, self.task_queue, self.result_queue),
        }
        for w in self.workers.values():
            w.start()

    def submit(self, name, agent_type, payload, priority=5):
        with self._lock:
            self._task_counter += 1
            task = Task(self._task_counter, name, agent_type, payload, priority)
            # Lower number = higher priority in PriorityQueue
            self.task_queue.put((priority, task))
            self.db.add_agent_message(0, "submitted", f"Task #{task.id}: {name} -> {agent_type}")
            return task.id

    def get_results(self, timeout=0.1):
        results = []
        while not self.result_queue.empty():
            try:
                results.append(self.result_queue.get_nowait())
            except queue.Empty:
                break
        return results

    def get_pending_count(self):
        return self.task_queue.qsize()

    def stop_all(self):
        for w in self.workers.values():
            w.stop()
        for w in self.workers.values():
            w.join(timeout=2)
