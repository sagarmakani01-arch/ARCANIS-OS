from typing import Dict, Any, Optional, List
from arcanis_inference.config import InferenceConfig
from arcanis_inference.backends import InferenceBackend
from arcanis_inference.backends.dummy import DummyBackend
from arcanis_inference.models.intent import IntentClassifier
from arcanis_inference.models.generator import TextGenerator


class InferenceEngine:
    def __init__(self, config: Optional[InferenceConfig] = None):
        self.config = config or InferenceConfig()
        self._backend: Optional[InferenceBackend] = None
        self._intent_classifier: Optional[IntentClassifier] = None
        self._text_generator: Optional[TextGenerator] = None
        self._initialized = False

    def initialize(self, backend: Optional[InferenceBackend] = None) -> None:
        self._backend = backend or DummyBackend()
        self._intent_classifier = IntentClassifier(self.config)
        self._text_generator = TextGenerator(self.config, self._backend)
        self._initialized = True

    def load_model(self, model_path: Optional[str] = None) -> None:
        if not self._initialized:
            raise RuntimeError("Engine not initialized. Call initialize() first.")
        path = model_path or self.config.model_path
        if not path:
            raise ValueError("No model path specified")
        self._backend.load_model(
            path,
            context_length=self.config.context_length,
            n_threads=self.config.n_threads,
        )

    def process(self, user_input: str, context: Optional[str] = None) -> Dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("Engine not initialized. Call initialize() first.")

        intent, confidence = self._intent_classifier.classify(user_input)

        response = self._text_generator.generate(user_input, context=context)

        return {
            "input": user_input,
            "intent": intent,
            "confidence": confidence,
            "response": response,
            "backend": self._backend.get_model_info(),
        }

    def classify_intent(self, text: str) -> Dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("Engine not initialized.")
        intent, confidence = self._intent_classifier.classify(text)
        return {"intent": intent, "confidence": confidence}

    def generate_command(self, intent: str, user_input: str) -> str:
        if not self._initialized:
            raise RuntimeError("Engine not initialized.")
        return self._text_generator.generate_command(intent, user_input)

    def generate_explanation(self, code: str) -> str:
        if not self._initialized:
            raise RuntimeError("Engine not initialized.")
        return self._text_generator.generate_explanation(code)

    def generate_plan(self, task: str) -> str:
        if not self._initialized:
            raise RuntimeError("Engine not initialized.")
        return self._text_generator.generate_plan(task)

    def get_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._initialized,
            "model_loaded": self._backend.is_loaded() if self._backend else False,
            "backend": self._backend.get_model_info() if self._backend else None,
            "config": {
                "model_type": self.config.model_type,
                "backend": self.config.backend,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
        }

    def shutdown(self) -> None:
        if self._backend and self._backend.is_loaded():
            self._backend.unload_model()
        self._initialized = False
