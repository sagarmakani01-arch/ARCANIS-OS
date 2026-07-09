# Microkernel Architecture Survey

**Path:** `00_Documentation/research/microkernel-survey.md`
**Phase:** 1 — Q1 2027
**Status:** Complete

---

## Executive Summary

This survey evaluates microkernel architectures for the Arcanis OS. The goal is a minimal kernel that provides only mechanism (IPC, scheduling, memory management) while policies live in user-space servers.

## Architectures Evaluated

### 1. L4 Microkernel Family

| Variant | Key Feature | IPC Latency | Lines of Code |
|---------|-------------|-------------|---------------|
| L4Ka::Haiku | Type-safe, C++ | ~2μs | ~10K |
| seL4 | Formally verified, C | ~5μs | ~10K |
| Fiasco.OC | OCaml-verified, C++ | ~4μs | ~25K |
| NOVA | Type-0 hypervisor, C++ | ~3μs | ~15K |

**Verdict:** L4 provides the best performance/verification tradeoff. seL4's formal verification is aspirational but adds complexity.

### 2. Minix 3

- **Approach:** Driver isolation via restartable server processes
- **Strength:** Self-healing drivers, proven reliability
- **Weakness:** Higher IPC overhead (~15μs), monolithic driver model
- **Relevance:** Good reference for driver fault containment

### 3. Zircon (Fuchsia)

- **Approach:** Capability-based, handle-based IPC
- **Strength:** Modern design, GPU-aware scheduling
- **Weakness:** Tightly coupled to Fuchsia ecosystem
- **Relevance:** Capability model is directly applicable

### 4. Plan 9

- **Approach:** Everything is a file (9P protocol)
- **Strength:** Elegant namespace model
- **Weakness:** No memory protection between namespaces
- **Relevance:** Namespace design influences our semantic FS

## Design Decisions for ArcanisKernel

Based on this survey, ArcanisKernel should adopt:

1. **L4-style synchronous IPC** — Short message passing, no kernel-mediated scheduling for server threads
2. **Capability-based security** — Inspired by Zircon's handle model
3. **Minimal syscall surface** — ~15 syscalls total (map, send, receive, create, destroy, yield, wait, etc.)
4. **User-space drivers** — Following Minix 3's isolation model
5. **Formal verification path** — Design for verifiability from day one (seL4-style proof obligations)

## Recommended Architecture

```
┌─────────────────────────────────────────┐
│              User Space                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  Driver   │ │  Driver   │ │  Shell    │ │
│  │  Server   │ │  Server   │ │  Server   │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │             │             │        │
│  ─────┼─────────────┼─────────────┼──────  │
│       │  IPC (synchronous, capability-gated)│
│  ─────┼─────────────┼─────────────┼──────  │
│  ┌────┴─────────────┴─────────────┴────┐  │
│  │         Microkernel                  │  │
│  │  ┌──────────┐ ┌──────────┐         │  │
│  │  │ Scheduler │ │  VMM     │         │  │
│  │  └──────────┘ └──────────┘         │  │
│  │  ┌──────────┐ ┌──────────┐         │  │
│  │  │  IPC     │ │  Timer   │         │  │
│  │  └──────────┘ └──────────┘         │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Comparison Matrix

| Criteria | L4 | Minix3 | Zircon | Plan9 | **Arcanis** |
|----------|-----|--------|--------|-------|-------------|
| IPC latency | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★★★☆☆ | Target: ★★★★☆ |
| Security | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | Target: ★★★★★ |
| Verifiability | ★★★★★ | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ | Target: ★★★★☆ |
| Driver isolation | ★★☆☆☆ | ★★★★★ | ★★★☆☆ | ★★☆☆☆ | Target: ★★★★★ |
| AI integration | ★☆☆☆☆ | ★☆☆☆☆ | ★★☆☆☆ | ★☆☆☆☆ | Target: ★★★★★ |

---

*Research conducted Q1 2027. Findings inform Phase 2 kernel redesign.*
