"""ArcanisInference - Lightweight on-device inference engine for Arcanis."""

__version__ = "0.1.0"

from arcanis_inference.engine import InferenceEngine
from arcanis_inference.config import InferenceConfig

__all__ = ["InferenceEngine", "InferenceConfig"]
