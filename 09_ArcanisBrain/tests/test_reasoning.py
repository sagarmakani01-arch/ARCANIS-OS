import pytest
from arcanis_brain import ArcanisBrain, BrainConfig
from arcanis_brain.reasoning.planner import Planner
from arcanis_brain.reasoning.decision import DecisionEngine
from arcanis_brain.reasoning.solver import Solver
from arcanis_brain.core.types import Task


@pytest.fixture
def brain():
    return ArcanisBrain(BrainConfig())


@pytest.mark.asyncio
async def test_planner_creates_plan(brain):
    planner = Planner(brain)
    task = Task(objective="Find information about AI")
    plan = await planner.create_plan(task, {})
    assert len(plan.steps) > 0
    assert plan.objective == "Find information about AI"


@pytest.mark.asyncio
async def test_decision_scoring(brain):
    engine = DecisionEngine(brain)
    context = {"goal": "test"}
    options = [
        {"name": "A", "confidence": 0.9, "relevance": 0.8},
        {"name": "B", "confidence": 0.5, "relevance": 0.5},
    ]
    chosen = await engine.decide(context, options)
    assert chosen["name"] == "A"


@pytest.mark.asyncio
async def test_solver_strategies(brain):
    solver = Solver(brain)
    result = await solver.solve({"type": "complex", "description": "test", "parts": [{"description": "part1"}]}, {})
    assert result["strategy"] == "decomposition"
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_task_classification(brain):
    planner = Planner(brain)
    task = Task(objective="Write a Python function")
    plan = await planner.create_plan(task, {})
    assert len(plan.steps) >= 2
