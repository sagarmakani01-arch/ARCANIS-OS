from typing import List, Dict, Any
from arcanis_inference.backends import InferenceBackend


class DummyBackend(InferenceBackend):
    def __init__(self):
        self._loaded = False
        self._model_path = ""

    def load_model(self, model_path: str, **kwargs) -> None:
        self._model_path = model_path
        self._loaded = True

    def generate(self, prompt: str, max_tokens: int = 256,
                 temperature: float = 0.7, **kwargs) -> str:
        if not self._loaded:
            raise RuntimeError("Model not loaded")
        tokens = self.tokenize(prompt)
        response_tokens = tokens[:max_tokens]
        return self.detokenize(response_tokens)

    def tokenize(self, text: str) -> List[int]:
        return [ord(c) for c in text]

    def detokenize(self, tokens: List[int]) -> str:
        return "".join(chr(t) if 32 <= t < 127 else "?" for t in tokens)

    def unload_model(self) -> None:
        self._loaded = False
        self._model_path = ""

    def is_loaded(self) -> bool:
        return self._loaded

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "dummy",
            "model_path": self._model_path,
            "loaded": self._loaded,
        }
