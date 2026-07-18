import os
from datetime import datetime
from .database import Database


PROJECTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".ecosystem", "projects")


class ProjectManager:
    def __init__(self):
        self.db = Database()
        os.makedirs(PROJECTS_DIR, exist_ok=True)

    def create(self, name, description="", priority="medium"):
        pid = self.db.add_project(name, description, "active", priority)
        if pid:
            proj_dir = os.path.join(PROJECTS_DIR, name.replace(" ", "_"))
            os.makedirs(proj_dir, exist_ok=True)
            self.db.add_memory(f"Created project: {name}", "projects")
        return pid

    def list_all(self, status=""):
        return self.db.get_projects(status)

    def get(self, pid):
        projects = self.db.get_projects()
        for p in projects:
            if p["id"] == pid:
                p["tasks"] = self.db.get_tasks(pid)
                return p
        return None

    def update(self, pid, **kw):
        self.db.update_project(pid, **kw)

    def archive(self, pid):
        self.db.update_project(pid, status="archived")

    def add_task(self, project_id, title, description="", priority="medium"):
        tid = self.db.add_task(project_id, title, description, priority)
        if tid:
            self.db.add_memory(f"Added task '{title}' to project {project_id}", "projects")
        return tid

    def get_tasks(self, project_id=-1, status=""):
        return self.db.get_tasks(project_id, status)

    def complete_task(self, tid):
        self.db.update_task(tid, status="completed")

    def get_stats(self):
        return self.db.get_stats()
