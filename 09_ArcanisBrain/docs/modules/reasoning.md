# Reasoning Module

The Reasoning module handles task planning, decision making, and problem solving.

## Planner

Decomposes user objectives into executable step sequences. Classifies tasks into types (retrieval, analysis, generation, computation, general) and builds dependency graphs.

```python
planner = Planner(brain)
plan = await planner.create_plan(task, context)
```

## DecisionEngine

Scores and selects between options based on confidence, relevance, and risk factors.

```python
engine = DecisionEngine(brain)
chosen = await engine.decide(context, options)
```

## Solver

Applies multi-strategy problem solving: decomposition, analogy, search, heuristic.

```python
solver = Solver(brain)
result = await solver.solve(problem, context)
```
