# Ecosystem Architecture Overview

**Path:** `architecture/ecosystem-overview.md`  
**Version:** 0.5.0  
**Status:** Active

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

## Project Index

| ID | Project | Layer | Status | Language |
|---|---|---|---|---|
| 00 | Documentation | Foundation | **Active** | Markdown |
| 01 | ArcanisLang | Foundation | **Implemented** | Python |
| 02 | ArcanisCompiler | Foundation | **Implemented** | TypeScript |
| 03 | ArcanisVM | Core | **Implemented** | C |
| 04 | ArcanisIDE | Foundation | **Implemented** | TypeScript |
| 05 | ArcanisBuild | Foundation | **Implemented** | Python |
| 06 | ArcanisPackageManager | Foundation | **Implemented** | JavaScript |
| 07 | ArcanisDatabase | Core | **Implemented** | Python |
| 08 | ArcanisKnowledgeGraph | Core | **Implemented** | Python |
| 09 | ArcanisBrain | AI | **Implemented** | Python |
| 10 | ArcanisAgents | AI | **Implemented** | Python |
| 11 | ArcanisMemory | AI | **Implemented** | Python |
| 12 | ArcanisShell | Systems | **Implemented** | Python |
| 13 | ArcanisAutomation | Systems | **Implemented** | Python |
| 14 | ArcanisVoice | Interface | **Implemented** | Python |
| 15 | ArcanisVision | Interface | **Implemented** | Python |
| 16 | ArcanisUI | Interface | **Implemented** | TypeScript |
| 17 | ArcanisDesktop | Interface | **Implemented** | JavaScript |
| 18 | ArcanisKernel | Core | **Implemented** | C/ASM |
| 19 | ArcanisDrivers | Core | **Implemented** | C |
| 20 | ArcanisFileSystem | Systems | **Implemented** | Python |
| 21 | ArcanisNetwork | Systems | **Implemented** | TypeScript |
| 22 | ArcanisSecurity | Systems | **Implemented** | Python |
| 23 | ArcanisOS | Core | **Implemented** | TypeScript |
| 24 | SharedLibraries | Core | **Implemented** | C# |
| 25 | DeveloperTools | Foundation | **Implemented** | TypeScript |
| 26 | Testing | Foundation | **Implemented** | TypeScript |
| 27 | Experiments | Research | Planned | — |
| 27 | ArcanisExperiments | Systems | **Implemented** | Python |
| 28 | ArcanisResearch | Research | **Implemented** | Python |
| 29 | ArcanisAssets | Foundation | **Implemented** | Python |
| 30 | ArcanisRuntime | Core | **Implemented** | C |
| 30 | Scripts | Foundation | Partial | Shell |
| 31 | ArcanisContainer | Systems | **Implemented** | TypeScript |
| 32 | ArcanisCloud | Systems | **Implemented** | TypeScript |
| 33 | ArcanisAPI | Systems | **Implemented** | TypeScript |
| 34 | ArcanisAuth | Systems | **Implemented** | TypeScript |
| 35 | ArcanisConfig | Systems | **Implemented** | TypeScript |
| 36 | ArcanisLogs | Systems | **Implemented** | TypeScript |
| 37 | ArcanisBackup | Systems | **Implemented** | TypeScript |
| 38 | ArcanisCDN | Systems | **Implemented** | TypeScript |
| 39 | ArcanisGraphQL | Systems | **Implemented** | TypeScript |
| 41 | ArcanisSemanticFS | Systems | **Implemented** | Python |
| 50 | ArcanisSecurity | Systems | **Implemented** | Python |
| 60 | ArcanisInference | AI | **Implemented** | Python |
| 62 | ArcanisFederated | AI | **Implemented** | Python |
| 90 | ArcanisHAL | Hardware | **Implemented** | Python |
| 91 | ArcanisDriverSynth | Hardware | **Implemented** | Python |
| 99 | ArcanisIntegration | Testing | **Implemented** | Python |
| 10 | ArcanisAgentSDK | AI | **Implemented** | Python |
| 22 | ArcanisAIScheduler | Core | **Implemented** | Python |
| 33 | ArcanisDevAPI | Systems | **Implemented** | Python |
| 06 | ArcanisPkgManager | Foundation | **Implemented** | Python |
| 04 | ArcanisCLI | Foundation | **Implemented** | Python |

### Summary

- **Implemented:** 49 projects with real code
- **Design:** 0 projects
- **Planned/Minimal:** 0 projects

## Communication Architecture

Projects communicate through:
1. **Shared memory channels** — High-performance, zero-copy IPC between kernel-adjacent projects
2. **Message buses** — Pub/sub event system for system-level notifications
3. **Contract APIs** — Versioned, schema-validated RPC for layer-crossing calls
4. **File system pipes** — For user-facing data flow (pipe semantics extended)

## Design Tenets

- **Separation of mechanism and policy** — Kernel provides mechanisms; user-space sets policies
- **Capability-based security** — No global root; every process has minimum necessary capabilities
- **Fail-fast with recovery** — Components crash independently and restart without cascading
- **Telemetry everywhere** — Every subsystem emits structured, privacy-preserving metrics
- **No single point of AI** — Intelligence is distributed; no model is a bottleneck

---

*Architecture is never finished. It evolves as understanding deepens.*
