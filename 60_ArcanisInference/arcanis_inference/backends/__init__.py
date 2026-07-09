from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class InferenceBackend(ABC):
    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        pass

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 256,
                 temperature: float = 0.7, **kwargs) -> str:
        pass

    @abstractmethod
    def tokenize(self, text: str) -> List[int]:
        pass

    @abstractmethod
    def detokenize(self, tokens: List[int]) -> str:
        pass

    @abstractmethod
    def unload_model(self) -> None:
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        pass
