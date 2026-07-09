# Research: Compilers

**Path:** `research/compilers.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Research Direction

The Arcanis compiler research focuses on **AI-driven optimization** and **self-hosting compilation**. We aim to build a compiler that learns optimization strategies rather than relying solely on hardcoded heuristics.

## Existing Compilers to Study

### Production Compilers
- **LLVM / Clang** — Industry standard, extensive optimization pipeline, Rust backend
- **GCC** — Mature, many backends, aggressive optimization
- **Rustc** — Rust compiler, borrow checker, MIR/HIR IR

### Research Compilers
- **MLIR** (Multi-Level IR) — Progressive lowering, ideal for heterogeneous compilation
- **Cranelift** — Fast code generation, suitable for JIT
- **Efficient MLIR** — MLIR with ML-driven optimization
- **Tiramisu** — Polyhedral compiler for high-performance code generation
- **ML compiler** — Learned optimization for ML workloads

### AI-Driven Compilers
- **Vellvm / Llvm-mca** — Formal semantics for LLVM
- **Optz** — Machine learning for LLVM pass ordering
- **ProGraML** — Graph neural networks for compiler optimization
- **CompilerGym** — RL environment for compiler optimization research

## Arcanis Compiler Goals

1. **AI-driven pass ordering** — Learn optimal pass sequences per function/module
2. **Learned cost models** — Replace heuristic-based inlining/unrolling decisions
3. **Type-driven optimization** — Leverage Rust's type system for better analysis
4. **Self-hosting** — The Arcanis compiler must compile itself
5. **Kernel-aware optimization** — Special passes for kernel code (no FP, no recursion limits)

## Intermediate Representation (IR)

We will design a **layered IR** system:

```
Source (Rust/C)
    │
    ▼
Level 1: High-Level IR (HIR)  — Preserves source semantics, types, borrows
    │
    ▼
Level 2: Mid-Level IR (MIR)   — Control flow graph, SSA form, no types
    │
    ▼
Level 3: Low-Level IR (LIR)   — Target-specific, register allocation ready
    │
    ▼
Machine Code
```

## AI Integration Points

| Compiler Phase | AI Technique | Benefit |
|---|---|---|
| **Pass ordering** | Reinforcement learning | Faster code, smaller binaries |
| **Inlining decisions** | Cost model (ML) | Better size/speed trade-offs |
| **Register allocation** | Graph neural networks | Improved spill decisions |
| **Loop transformations** | Polyhedral + ML | Optimized cache behavior |
| **Vectorization** | Pattern recognition | Auto-SIMD |

## Self-Hosting Requirement

The Arcanis compiler must:

1. Be written in Rust (which the compiler itself will support)
2. Compile its own source code
3. Produce bit-identical output when compiling itself (reproducible builds)
4. Be at least as fast as the reference compiler (rustc) for equivalent code

## Hardware Targets

- **x86-64** — Primary development target
- **ARM64 (aarch64)** — Primary mobile/server target
- **RISC-V** — Open architecture target, long-term strategic
- **WebAssembly** — Sandboxed execution target

---

*A compiler is not a tool. It is a bridge between human intent and machine execution.*
