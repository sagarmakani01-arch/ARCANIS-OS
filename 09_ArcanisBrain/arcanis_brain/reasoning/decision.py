from typing import Any
import json


class DecisionEngine:
    def __init__(self, brain):
        self.brain = brain
        self._history: list[dict] = []

    async def decide(self, context: dict, options: list[dict]) -> dict:
        scored = []
        for option in options:
            score = self._score_option(option, context)
            scored.append((score, option))

        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[0][1] if scored else {}

        self._history.append({
            "context": context,
            "options": options,
            "chosen": chosen,
            "reasoning": self._explain_choice(chosen, scored),
        })

        return chosen

    def _score_option(self, option: dict, context: dict) -> float:
        score = 0.5
        if "confidence" in option:
            score *= option["confidence"]
        if "relevance" in option:
            score *= option["relevance"]
        if "risk" in option:
            score *= (1.0 - option["risk"])
        return score

    def _explain_choice(self, chosen: dict, scored: list) -> str:
        if not chosen:
            return "No suitable option found"
        return f"Selected option with score {scored[0][0]:.2f}"

    def get_history(self) -> list[dict]:
        return self._history
