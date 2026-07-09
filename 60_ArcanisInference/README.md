# ArcanisInference

**Project ID:** 60-ArcanisInference
**Phase:** 1 — Research & Prototyping (Q3 2027)
**Status:** Prototype
**Language:** Python

## Overview

ArcanisInference is a lightweight, on-device inference engine designed for the Arcanis ecosystem. It provides intent classification, text generation, and task planning with support for multiple backends (llama.cpp, dummy for testing).

## Architecture

```
┌──────────────────────────────────────────┐
│           InferenceEngine                 │
├──────────────────────────────────────────┤
│  IntentClassifier  │  TextGenerator      │
│  • Pattern-based   │  • Prompt building   │
│  • Multi-class     │  • Context injection │
│  • Configurable    │  • Response cleaning │
├──────────────────────────────────────────┤
│           Backend Abstraction             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Dummy    │ │ llama.cpp│ │ (future) │ │
│  │ Backend  │ │ Backend  │ │ ONNX     │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────┘
```

## Quick Start

```bash
# Install
pip install -e .

# Classify intent
arcanis-inference classify "create a new file"

# Generate text (requires model)
arcanis-inference generate "write a hello world program" --model path/to/model.gguf

# Show status
arcanis-inference status
```

## API

```python
from arcanis_inference import InferenceEngine, InferenceConfig

config = InferenceConfig(model_type="tinyllama")
engine = InferenceEngine(config)
engine.initialize()
engine.load_model("path/to/model.gguf")

result = engine.process("organize my project files")
print(result["intent"])     # "file_operation"
print(result["response"])   # Generated response

engine.shutdown()
```

## Supported Intents

| Intent | Examples |
|--------|----------|
| `file_operation` | create, delete, move, copy, list, find files |
| `process_management` | run, kill, list processes |
| `system_info` | show system status, memory, disk |
| `code_generation` | write functions, classes, scripts |
| `code_explanation` | explain code, describe functions |
| `task_planning` | plan, organize, break down tasks |
| `question_answering` | what, how, why questions |
| `general` | Everything else |

## Testing

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

All rights reserved. ArcanisLabs — Sagar Makani.
