from arcanis_brain.reasoning.planner import Planner
from arcanis_brain.reasoning.decision import DecisionEngine
from arcanis_brain.reasoning.solver import Solver


class ReasoningModule:
    def __init__(self, brain):
        self.brain = brain
        self.planner = Planner(brain)
        self.decision = DecisionEngine(brain)
        self.solver = Solver(brain)

    def create_task(self, user_input: str, context: dict) -> "Task":
        from arcanis_brain.core.types import Task
        return Task(objective=user_input, context=context)

    async def plan(self, task: "Task", context: dict):
        return await self.planner.create_plan(task, context)

    def evaluate_step(self, step: dict, result: any):
        self.planner.evaluate(step, result)


__all__ = ["ReasoningModule", "Planner", "DecisionEngine", "Solver"]
