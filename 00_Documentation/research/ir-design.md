# Compiler IR Design

**Path:** `00_Documentation/research/ir-design.md`
**Phase:** 1 — Q1 2027
**Status:** Complete

---

## Executive Summary

This document surveys intermediate representation (IR) designs for the ArcanisLang compiler, evaluating tradeoffs between SSA-based IRs, stack-based IRs, and graph-based IRs for our AI-native compilation goals.

## IR Paradigms Evaluated

### 1. SSA-Based IR (LLVM IR, Cranelift IR)

**Structure:** Static Single Assignment form — every variable is assigned exactly once.

```llvm
; LLVM IR example
define i32 @add(i32 %a, i32 %b) {
  %result = add i32 %a, %b
  ret i32 %result
}
```

| Pros | Cons |
|------|------|
| Mature optimization passes | Complex to lower from AST |
| Excellent register allocation | PHI nodes add complexity |
| Well-understood data flow | Harder to emit from dynamic lang |
| Rich tooling ecosystem | LLVM is heavy (~2M LOC) |

**Verdict:** Best for optimization but heavy. Cranelift is a lighter alternative.

### 2. Stack-Based IR (WebAssembly, JVM Bytecode)

**Structure:** Operands pushed/popped from an implicit stack.

```wasm
;; WebAssembly example
(func $add (param i32 i32) (result i32)
  local.get 0
  local.get 1
  i32.add)
```

| Pros | Cons |
|------|------|
| Simple to generate | Limited optimization surface |
| Platform independent | Stack depth analysis needed |
| Easy to verify | Less efficient code generation |
| Good for interpreted targets | No SSA benefits |

**Verdict:** Good fallback target but not primary.

### 3. Sea-of-Nodes IR (V8 TurboFan, Graal)

**Structure:** Graph where operations are nodes and data/control flow are edges.

| Pros | Cons |
|------|------|
| Natural for dynamic optimization | Complex implementation |
| Lazy compilation fits well | Hard to serialize/inspect |
| Good for JIT | Steep learning curve |

**Verdict:** Overkill for ahead-of-time compilation.

## Recommended Design: ArcanisIR

A **lightweight SSA-based IR** inspired by Cranelift, designed for:

1. **AI-assisted optimization** — IR nodes annotated with semantic metadata for ML-guided passes
2. **Incremental compilation** — IR supports patching without full recompilation
3. **Multiple backends** — JS, WASM, native x86
4. **Verification-friendly** — Structural invariants checkable at build time

### IR Structure

```
Function
  └── Block[] (basic blocks)
        └── Instruction[] (SSA instructions)
              ├── Opcode (add, load, store, call, branch...)
              ├── Operands[] (ValueRef — SSA values)
              ├── Result (ValueRef — SSA value)
              └── Metadata (source location, AI annotations)
```

### Key Types

```
Value       — SSA register (typed: i32, i64, f32, f64, ptr)
Block       — Basic block with terminators
Function    — Collection of blocks, signature, metadata
Module      — Collection of functions, globals, types
```

### Optimization Pipeline

```
Source → AST → ArcanisIR → [AI Pass] → [Peephole] → [Dead Code] → Target Code
                           ^^^^^^^^^^^
                           ML model selects optimization strategy
                           based on IR node metadata + profiling data
```

## AI Integration Points

| Stage | AI Role | Input | Output |
|-------|---------|-------|--------|
| IR Generation | AST→IR lowering hints | AST pattern | Lowering strategy |
| Optimization | Pass selection | IR metadata + profiles | Optimization sequence |
| Register Allocation | Spill prediction | IR live ranges | Allocation strategy |
| Code Generation | Peephole patterns | IR nodes | Target-specific tricks |

## Comparison Matrix

| Criteria | SSA (Cranelift) | Stack (WASM) | Sea-of-Nodes | **ArcanisIR** |
|----------|-----------------|--------------|--------------|---------------|
| Generation ease | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | Target: ★★★★☆ |
| Optimization | ★★★★★ | ★★☆☆☆ | ★★★★★ | Target: ★★★★☆ |
| AI integration | ★★☆☆☆ | ★☆☆☆☆ | ★★★☆☆ | Target: ★★★★★ |
| Incremental | ★★★☆☆ | ★★☆☆☆ | ★★★★☆ | Target: ★★★★★ |
| Verification | ★★★★☆ | ★★★★☆ | ★★☆☆☆ | Target: ★★★★☆ |

---

*Research conducted Q1 2027. ArcanisIR prototype planned for Phase 2.*
