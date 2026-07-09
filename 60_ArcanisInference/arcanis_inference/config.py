from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InferenceConfig:
    model_path: Optional[str] = None
    model_type: str = "tinyllama"
    backend: str = "llamacpp"
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    context_length: int = 2048
    n_threads: int = 4
    use_gpu: bool = False
    quantization: str = "int8"
    batch_size: int = 1
    timeout_seconds: float = 30.0
    cache_size: int = 100
    intent_categories: list = field(default_factory=lambda: [
        "file_operation", "process_management", "system_info",
        "code_generation", "code_explanation", "task_planning",
        "question_answering", "general"
    ])
