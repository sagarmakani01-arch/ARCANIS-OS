from typing import Any, Optional
from datetime import datetime, timezone
from arcanis_brain.core.types import Task, TaskStatus, AgentIdentity, Message, MessageRole


class TaskDelegator:
    def __init__(self, brain):
        self.brain = brain
        self._active_tasks: dict[str, Task] = {}

    async def execute(self, agent: AgentIdentity, step: dict, context) -> Task:
        task = Task(
            objective=step.get("description", ""),
            status=TaskStatus.IN_PROGRESS,
            assigned_agent=agent.name,
            required_tools=[step.get("tool", "")],
        )
        self._active_tasks[task.task_id] = task

        safe = await self.brain.security.check_permission(agent, step)
        if not safe.granted:
            task.status = TaskStatus.FAILED
            task.error = safe.reason
            return task

        self.brain.event_bus.emit("task.delegated", task)

        try:
            result = await self._dispatch(agent, step, context)
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)

        return task

    async def _dispatch(self, agent: AgentIdentity, step: dict, context) -> Any:
        tool = step.get("tool", "reason")
        return await self.brain.agents.tools.execute(tool, step, context)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._active_tasks.get(task_id)

    def get_active_tasks(self) -> list[Task]:
        return [t for t in self._active_tasks.values() if t.status == TaskStatus.IN_PROGRESS]
