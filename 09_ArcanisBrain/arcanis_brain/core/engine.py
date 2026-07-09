from arcanis_brain.config import BrainConfig
from arcanis_brain.core.events import EventBus
from arcanis_brain.core.types import Context, Message, MessageRole, Task, TaskStatus
from arcanis_brain.reasoning import ReasoningModule
from arcanis_brain.memory import MemoryModule
from arcanis_brain.agents import AgentModule
from arcanis_brain.personality import PersonalityModule
from arcanis_brain.security import SecurityModule


class ArcanisBrain:
    def __init__(self, config: BrainConfig | None = None):
        self.config = config or BrainConfig()
        self.event_bus = EventBus()
        self.context = Context()

        self.reasoning = ReasoningModule(self)
        self.memory = MemoryModule(self)
        self.agents = AgentModule(self)
        self.personality = PersonalityModule(self)
        self.security = SecurityModule(self)

        self._initialized = False

    async def initialize(self):
        await self.memory.initialize()
        await self.agents.initialize()
        self._initialized = True
        self.event_bus.emit("brain.initialized", source="engine")

    async def process(self, user_input: str, user_id: str = "anonymous") -> str:
        self.context.user_id = user_id
        self.context.conversation_history.append(
            Message(role=MessageRole.USER, content=user_input)
        )

        safe = await self.security.check_input(user_input, self.context)
        if not safe.allowed:
            return safe.message

        profile = self.personality.get_profile(user_id)
        adapted_input = self.personality.adapt_input(user_input, profile)

        recent = await self.memory.get_relevant_context(adapted_input)
        task = self.reasoning.create_task(adapted_input, recent)
        self.context.active_task = task
        self.event_bus.emit("task.created", task)

        try:
            plan = await self.reasoning.plan(task, recent)
            for step in plan.steps:
                agent = await self.agents.select_agent(step)
                result = await self.agents.execute(agent, step, self.context)
                task.subtasks.append(result.task_id)
                self.reasoning.evaluate_step(step, result)

            response = await self._compose_response(task, profile)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            response = f"I encountered an error while processing your request: {e}"
            self.event_bus.emit("task.failed", task)

        styled = self.personality.style_response(response, profile)
        self.context.conversation_history.append(
            Message(role=MessageRole.AGENT, content=styled)
        )
        await self.memory.store_interaction(user_input, styled, user_id)
        self.event_bus.emit("task.completed", task)

        return styled

    async def _compose_response(self, task: Task, profile: dict) -> str:
        return task.result or "Task completed successfully."

    async def shutdown(self):
        await self.memory.persist()
        await self.agents.shutdown()
        self.event_bus.emit("brain.shutdown", source="engine")
