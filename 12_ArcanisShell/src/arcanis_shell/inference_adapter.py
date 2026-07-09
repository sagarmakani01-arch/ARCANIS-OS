"""ArcanisShell — Inference engine integration.

Provides a BrainAdapter backed by 60_ArcanisInference, enabling the shell
to use the real inference engine for intent classification and text generation
instead of the local heuristic stub.
"""

from __future__ import annotations

from typing import Any

from .integration import BrainAdapter, BrainResponse


class InferenceAdapter(BrainAdapter):
    """Brain adapter backed by ArcanisInference.

    Wraps InferenceEngine to provide NL understanding for the shell.
    Falls back to LocalBrainAdapter behavior if the engine is unavailable.
    """

    def __init__(self, model_path: str | None = None, backend: str = "llamacpp"):
        self._engine = None
        self._model_path = model_path
        self._backend = backend
        self._initialized = False

    def _ensure_engine(self) -> Any:
        if self._initialized:
            return self._engine

        try:
            from arcanis_inference import InferenceEngine, InferenceConfig
            from arcanis_inference.backends.dummy import DummyBackend

            config = InferenceConfig(
                model_type="tinyllama",
                backend=self._backend,
                max_tokens=256,
                temperature=0.7,
            )
            self._engine = InferenceEngine(config)

            if self._model_path:
                from arcanis_inference.backends.llamacpp import llamaCppBackend
                backend_instance = llamaCppBackend()
                self._engine.initialize(backend=backend_instance)
                self._engine.load_model(self._model_path)
            else:
                self._engine.initialize(backend=DummyBackend())

            self._initialized = True
            return self._engine
        except ImportError:
            self._initialized = True
            self._engine = None
            return None

    def understand(self, request: str, context: dict[str, Any]) -> BrainResponse:
        engine = self._ensure_engine()

        if engine is None:
            return self._fallback(request, context)

        try:
            result = engine.process(request, context=str(context))
            intent = result.get("intent", "general")
            confidence = result.get("confidence", 0.5)
            response_text = result.get("response", "")

            steps = self._intent_to_steps(intent, request, context)

            return BrainResponse(
                intent=intent,
                plan_steps=steps,
                explanation=response_text or f"Intent: {intent} (confidence: {confidence:.0%})",
                confidence=confidence,
            )
        except Exception:
            return self._fallback(request, context)

    def _intent_to_steps(
        self, intent: str, request: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        cwd = context.get("cwd", ".")

        if intent == "file_operation":
            if any(w in request.lower() for w in ("create", "new", "make")):
                return [{"description": "Create file", "command": f"touch {request.split()[-1]}", "risk": "low"}]
            if any(w in request.lower() for w in ("list", "show", "ls")):
                return [{"description": "List files", "command": "ls", "risk": "safe"}]
            if any(w in request.lower() for w in ("delete", "remove", "rm")):
                return [{"description": "Remove file", "command": f"rm {request.split()[-1]}", "risk": "medium"}]
            if any(w in request.lower() for w in ("find", "search")):
                return [{"description": "Search files", "command": f"find . -name '*{request.split()[-1]}*'", "risk": "safe"}]
            return [{"description": "List files", "command": "ls", "risk": "safe"}]

        if intent == "process_management":
            if any(w in request.lower() for w in ("list", "show", "ps")):
                return [{"description": "List processes", "command": "ps", "risk": "safe"}]
            if any(w in request.lower() for w in ("kill", "stop")):
                return [{"description": "Kill process", "command": "kill", "risk": "high"}]
            return [{"description": "Run program", "command": request, "risk": "medium"}]

        if intent == "system_info":
            return [{"description": "Show system info", "command": "sysinfo", "risk": "safe"}]

        if intent == "code_generation":
            return [{"description": "Generate code", "command": f"echo 'TODO: code gen for: {request}'", "risk": "safe"}]

        if intent == "code_explanation":
            return [{"description": "Explain code", "command": f"echo 'TODO: explanation for: {request}'", "risk": "safe"}]

        if intent == "task_planning":
            return [{"description": "Plan task", "command": f"echo 'TODO: plan for: {request}'", "risk": "safe"}]

        return [{"description": f"Process: {request}", "command": f"echo {request!r}", "risk": "safe"}]

    def _fallback(self, request: str, context: dict[str, Any]) -> BrainResponse:
        from .integration import LocalBrainAdapter
        return LocalBrainAdapter().understand(request, context)
