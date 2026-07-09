from typing import Any


class Solver:
    def __init__(self, brain):
        self.brain = brain
        self._strategies = {
            "decomposition": self._solve_by_decomposition,
            "analogy": self._solve_by_analogy,
            "search": self._solve_by_search,
            "heuristic": self._solve_by_heuristic,
        }

    async def solve(self, problem: dict, context: dict) -> dict:
        strategy = self._select_strategy(problem)
        solver = self._strategies.get(strategy, self._solve_by_decomposition)
        result = await solver(problem, context)

        return {
            "problem": problem.get("description", ""),
            "strategy": strategy,
            "solution": result,
            "confidence": self._calculate_confidence(result),
        }

    def _select_strategy(self, problem: dict) -> str:
        if problem.get("type") == "complex":
            return "decomposition"
        if problem.get("type") == "novel":
            return "analogy"
        if problem.get("type") == "optimization":
            return "heuristic"
        return "search"

    async def _solve_by_decomposition(self, problem: dict, context: dict) -> Any:
        parts = problem.get("parts", [problem])
        solutions = []
        for part in parts:
            solutions.append(await self._solve_by_search(part, context))
        return {"parts": solutions, "composition": " - ".join(str(s) for s in solutions)}

    async def _solve_by_analogy(self, problem: dict, context: dict) -> Any:
        familiar = context.get("similar_problems", [])
        if familiar:
            return {"approach": "analogy", "source": familiar[0], "adaptation": problem}
        return await self._solve_by_search(problem, context)

    async def _solve_by_search(self, problem: dict, context: dict) -> Any:
        return {"status": "analyzed", "insights": [f"Evaluated: {problem.get('description', 'unknown')}"]}

    async def _solve_by_heuristic(self, problem: dict, context: dict) -> Any:
        return {"status": "optimized", "approach": "heuristic", "efficiency": "high"}

    def _calculate_confidence(self, solution: Any) -> float:
        return 0.85
