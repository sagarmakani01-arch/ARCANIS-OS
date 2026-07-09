from typing import Optional
from arcanis_inference.config import InferenceConfig
from arcanis_inference.backends import InferenceBackend


class TextGenerator:
    def __init__(self, config: InferenceConfig, backend: InferenceBackend):
        self.config = config
        self.backend = backend
        self._system_prompt = (
            "You are Arcanis AI, an intelligent assistant built into the "
            "Arcanis operating system. You help users with file operations, "
            "system management, code generation, and task planning. "
            "Be concise and accurate."
        )

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt

    def generate(self, prompt: str, context: Optional[str] = None,
                 max_tokens: Optional[int] = None) -> str:
        if not self.backend.is_loaded():
            raise RuntimeError("No model loaded. Call engine.load_model() first.")

        full_prompt = self._build_prompt(prompt, context)
        tokens = max_tokens or self.config.max_tokens

        response = self.backend.generate(
            full_prompt,
            max_tokens=tokens,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            repeat_penalty=self.config.repeat_penalty,
        )
        return self._clean_response(response)

    def generate_command(self, intent: str, user_input: str) -> str:
        command_prompt = (
            f"Convert the following natural language request into a shell command.\n"
            f"Intent: {intent}\n"
            f"Request: {user_input}\n"
            f"Command:"
        )
        return self.generate(command_prompt, max_tokens=128)

    def generate_explanation(self, code: str) -> str:
        explain_prompt = (
            f"Explain what the following code does, line by line if helpful:\n\n"
            f"```\n{code}\n```\n\n"
            f"Explanation:"
        )
        return self.generate(explain_prompt, max_tokens=256)

    def generate_plan(self, task: str) -> str:
        plan_prompt = (
            f"Create a step-by-step plan to accomplish the following task:\n\n"
            f"Task: {task}\n\n"
            f"Plan:"
        )
        return self.generate(plan_prompt, max_tokens=512)

    def _build_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        parts = [f"System: {self._system_prompt}"]
        if context:
            parts.append(f"Context: {context}")
        parts.append(f"User: {prompt}")
        parts.append("Assistant:")
        return "\n\n".join(parts)

    def _clean_response(self, response: str) -> str:
        response = response.strip()
        prefixes = ["Assistant:", "AI:", "Arcanis:"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        return response
