# Ecosystem Architecture Overview

**Path:** `architecture/ecosystem-overview.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## High-Level Architecture

The Arcanis ecosystem is organized as a layered, modular system of projects. Each project occupies a well-defined layer and communicates with adjacent layers via formal contracts.

```
Project Index (00-99)
==========================
Layer 0:  Foundation  (00–19)  — Documentation, tooling, standards
Layer 1:  Core        (20–39)  — Kernel, runtime, memory management
Layer 2:  Systems     (40–59)  — Shell, file system, networking, security
Layer 3:  AI          (60–79)  — Models, orchestration, learning
Layer 4:  Interface   (80–89)  — UI, natural language, accessibility
Layer 5:  Hardware    (90–99)  — HAL, drivers, firmware
```

## Project Index (Planned)

| ID | Project | Layer | Status |
|---|---|---|---|
| 00 | Documentation | Foundation | **Active** |
| 01 | Development Tooling | Foundation | Planned |
| 02 | Build System | Foundation | Planned |
| 10 | Standards & Conventions | Foundation | Draft |
| 20 | Arcanis Microkernel | Core | Research |
| 21 | Memory Manager | Core | Research |
| 22 | Process Scheduler | Core | Research |
| 30 | Runtime Library | Core | Planned |
| 40 | Intent Shell | Systems | Research |
| 41 | Semantic File System | Systems | Research |
| 42 | Network Stack | Systems | Planned |
| 50 | Security Framework | Systems | Planned |
| 60 | Inference Engine | AI | Research |
| 61 | Policy & Planning | AI | Planned |
| 62 | Federated Learning | AI | Planned |
| 70 | User Modeling | AI | Planned |
| 80 | Natural Language Interface | Interface | Research |
| 81 | Accessibility Layer | Interface | Planned |
| 90 | Hardware Abstraction Layer | Hardware | Research |
| 91 | Driver Synthesis Engine | Hardware | Research |

## Communication Architecture

Projects communicate through:
1. **Shared memory channels** — High-performance, zero-copy IPC between kernel-adjacent projects
2. **Message buses** — Pub/sub event system for system-level notifications
3. **Contract APIs** — Versioned, schema-validated RPC for layer-crossing calls
4. **File system pipes** — For user-facing data flow (pipe semantics extended)

## Design Tenets

- **Separation of mechanism and policy** — Kernel provides mechanisms; user-space sets policies
- **Capability-based security** — No global root; every process has最小 necessary capabilities
- **Fail-fast with recovery** — Components crash independently and restart without cascading
- **Telemetry everywhere** — Every subsystem emits structured, privacy-preserving metrics
- **No single point of AI** — Intelligence is distributed; no model is a bottleneck

---

*Architecture is never finished. It evolves as understanding deepens.*
