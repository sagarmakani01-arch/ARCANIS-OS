from typing import List, Dict, Any
from arcanis_inference.backends import InferenceBackend


class llamaCppBackend(InferenceBackend):
    def __init__(self):
        self._loaded = False
        self._model_path = ""
        self._llama = None

    def load_model(self, model_path: str, **kwargs) -> None:
        try:
            from llama_cpp import Llama
            n_ctx = kwargs.get("context_length", 2048)
            n_threads = kwargs.get("n_threads", 4)
            self._llama = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_threads=n_threads,
                verbose=False,
            )
            self._loaded = True
            self._model_path = model_path
        except ImportError:
            raise ImportError(
                "llama-cpp-python is required. "
                "Install with: pip install llama-cpp-python"
            )

    def generate(self, prompt: str, max_tokens: int = 256,
                 temperature: float = 0.7, **kwargs) -> str:
        if not self._loaded or not self._llama:
            raise RuntimeError("Model not loaded")

        top_p = kwargs.get("top_p", 0.9)
        top_k = kwargs.get("top_k", 40)
        repeat_penalty = kwargs.get("repeat_penalty", 1.1)

        output = self._llama(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
        )
        return output["choices"][0]["text"]

    def tokenize(self, text: str) -> List[int]:
        if not self._llama:
            return [ord(c) for c in text]
        return self._llama.tokenize(text.encode("utf-8"))

    def detokenize(self, tokens: List[int]) -> str:
        if not self._llama:
            return "".join(chr(t) if 32 <= t < 127 else "?" for t in tokens)
        return self._llama.detokenize(tokens)

    def unload_model(self) -> None:
        self._llama = None
        self._loaded = False
        self._model_path = ""

    def is_loaded(self) -> bool:
        return self._loaded

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "backend": "llamacpp",
            "model_path": self._model_path,
            "loaded": self._loaded,
        }
