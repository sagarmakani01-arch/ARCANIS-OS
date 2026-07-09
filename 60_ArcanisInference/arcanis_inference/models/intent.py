import re
from typing import Dict, List, Tuple
from arcanis_inference.config import InferenceConfig


class IntentClassifier:
    def __init__(self, config: InferenceConfig):
        self.config = config
        self._patterns: Dict[str, List[str]] = {
            "file_operation": [
                r"\b(create|make|new)\b.*\b(file|directory|folder)\b",
                r"\b(delete|remove|rm)\b.*\b(file|directory|folder)\b",
                r"\b(move|mv|rename)\b.*\b(file|directory)\b",
                r"\b(copy|cp)\b.*\b(file|directory)\b",
                r"\b(list|ls|show)\b.*\b(file|directory|folder|contents)\b",
                r"\b(find|search|grep)\b.*\b(file|files|in)\b",
                r"\b(read|open|cat|view)\b.*\b(file)\b",
                r"\b(write|save|store)\b.*\b(to|file)\b",
            ],
            "process_management": [
                r"\b(run|execute|start|launch|launch)\b.*\b(program|process|app)\b",
                r"\b(stop|kill|terminate|close)\b.*\b(process|program|app)\b",
                r"\b(list|show|ps)\b.*\b(process|running)\b",
                r"\b(kill)\b.*\b(pid|process)\b",
            ],
            "system_info": [
                r"\b(what|show|get|display)\b.*\b(system|info|status|version)\b",
                r"\b(how much|memory|disk|space|cpu)\b",
                r"\b(whoami|hostname|date|time)\b",
            ],
            "code_generation": [
                r"\b(write|create|generate|build)\b.*\b(code|function|class|script|program)\b",
                r"\b(implement|code)\b.*\b(a|an|the)\b",
                r"\b(make|create)\b.*\b(a|an)\b.*\b(that|which)\b",
            ],
            "code_explanation": [
                r"\b(explain|describe|what does|how does)\b.*\b(code|this|it|function|class)\b",
                r"\b(how|why)\b.*\b(does|is|work|do)\b",
                r"\b(what is|what are)\b.*\b(this|that|it)\b",
            ],
            "task_planning": [
                r"\b(plan|organize|schedule|arrange)\b",
                r"\b(step[s]?|break down|decompose)\b",
                r"\b(how (to|do|can I|should I))\b",
                r"\b(help me (to|with|plan))\b",
            ],
            "question_answering": [
                r"\b(what|who|where|when|why|how)\b",
                r"\b(is|are|was|were|can|could|would|should)\b",
            ],
        }

    def classify(self, text: str) -> Tuple[str, float]:
        text_lower = text.lower().strip()
        scores: Dict[str, float] = {}

        for intent, patterns in self._patterns.items():
            score = 0.0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    score += 1.0
            if score > 0:
                scores[intent] = score / len(patterns)

        if not scores:
            return "general", 0.5

        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] * 2, 1.0)
        return best_intent, confidence

    def classify_with_threshold(self, text: str, threshold: float = 0.3) -> Tuple[str, float]:
        intent, confidence = self.classify(text)
        if confidence < threshold:
            return "general", confidence
        return intent, confidence

    def get_supported_intents(self) -> List[str]:
        return list(self._patterns.keys()) + ["general"]

    def add_pattern(self, intent: str, pattern: str) -> None:
        if intent not in self._patterns:
            self._patterns[intent] = []
        self._patterns[intent].append(pattern)
