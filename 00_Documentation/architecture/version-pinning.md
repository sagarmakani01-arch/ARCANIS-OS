# Version Pinning

All Arcanis modules pin to these minimum versions for release builds.

| Component | Min Version | Notes |
|-----------|-------------|-------|
| Python | 3.11.0 | Required for type union syntax |
| Make | 4.3 | Kernel build system |
| GCC | 13.0 | Cross-compiler for kernel |
| NASM | 2.16 | Kernel assembly |
| QEMU | 8.0 | Testing target |

## Python Dependencies (optional)

| Package | Version | Module | Purpose |
|---------|---------|--------|---------|
| llama-cpp-python | >=0.2.0 | 60-Inference | Local LLM inference |
| sentence-transformers | >=2.0 | 41-SemanticFS | Embedding model |
| numpy | >=1.24 | Multiple | Numerical ops |
| fastapi | >=0.100 | 33-DevAPI | REST API |
| uvicorn | >=0.23 | 33-DevAPI | ASGI server |
| pydantic | >=2.0 | Multiple | Data validation |

All core functionality works without optional dependencies.
