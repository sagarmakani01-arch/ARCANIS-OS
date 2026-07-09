# Research: AI Architectures

**Path:** `research/ai-architectures.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Core AI Requirements for Arcanis

1. **Sub-millisecond inference** — Must run inside kernel scheduling paths
2. **Small footprint** — Models must fit in L2/L3 cache for kernel-level use
3. **Explainable** — Every decision must be auditable
4. **Privacy-preserving** — User data never leaves the device
5. **Continuous learning** — Models adapt to user behavior over time
6. **Graceful degradation** — System functions without AI

## Model Architectures Under Evaluation

### Tiny LLMs / SLMs (<1B parameters)
- **Microsoft Phi-3 / Phi-4** — 3.8B, 14B; strong reasoning for size
- **Google Gemma 2 (2B)** — Lightweight, good instruction following
- **Llama 3.2 (1B, 3B)** — Strong open model family
- **SmolLM2** — 135M, 360M, 1.7B; extremely small
- **Use case:** Intent parsing, natural language shell, policy interpretation

### Lightweight Sequence Models
- **Mamba** — State space model, linear-time inference, competitive with transformers
- **RWKV** — RNN + transformer hybrid, constant memory inference
- **Use case:** Real-time system monitoring, anomaly detection in logs

### Specialized Architectures
- **Decision Transformers** — Reinforcement learning via sequence modeling
- **Perceiver IO** — Flexible input/output, good for sensor fusion
- **TinyBERT / DistilBERT** — Classification and intent recognition
- **Use case:** Scheduler optimization, resource allocation

### Neural-Symbolic Approaches
- **Neuro-symbolic reasoning** — Combine neural perception with symbolic logic
- **Graph Neural Networks** — For dependency and resource graph analysis
- **Use case:** Policy enforcement, capability derivation, formal reasoning

## Kernel-Level AI

The most challenging use case is running AI inside kernel scheduling paths:

**Constraints:**
- Inference budget: **<100µs** per invocation
- Memory budget: **<1MB** for model weights
- No floating-point hardware on all platforms (must support integer-only)

**Approaches:**
1. **Binary neural networks** — Extremely quantized (1-bit weights) for in-kernel classifiers
2. **Decision trees / random forests** — Fast, interpretable, small
3. **Lookup tables** — Precomputed policies for common patterns
4. **Tiny RNNs** — For sequential workload prediction (e.g., page access patterns)

## Training Strategy

1. **Offline pre-training** — Base models trained on public datasets
2. **On-device fine-tuning** — LoRA adapters for personalization
3. **Federated learning** — Optional, opt-in, for aggregate improvements
4. **User feedback loop** — Implicit (behavior) and explicit (ratings) signals

## Privacy Architecture

```
User Actions → Local Feature Extraction → On-Device Model
                                               │
                                     (No raw data leaves)
                                               │
                                    ┌──────────┴──────────┐
                                    ▼                     ▼
                              Local Improvement    Privacy-Preserving
                                                   Aggregates (optional)
```

---

*AI in the kernel is the hardest engineering challenge. It is also the most important.*
