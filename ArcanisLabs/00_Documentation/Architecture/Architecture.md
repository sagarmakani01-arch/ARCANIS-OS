# ArcanisLabs Global Architecture

## System Overview

ArcanisLabs is organized as a directed acyclic graph of dependencies. Each project builds upon the layers below it while maintaining independence.

```
APPLICATION LAYER
    ┌─────────────────────────────────────────────────────────────┐
    │                    23. ArcanisOS                            │
    │  Complete AI-native operating system                        │
    └─────────────────────────────────────────────────────────────┘

SYSTEM LAYER
    ┌──────┬──────┬──────┬──────┬──────┬──────┐
    │ 17   │ 18   │ 19   │ 20   │ 21   │ 22   │
    │Desktop│Kernel│Drivers│ FS   │Network│Security│
    └──────┴──────┴──────┴──────┴──────┴──────┘

FRAMEWORK LAYER
    ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐
    │ 09   │ 10   │ 11   │ 12   │ 13   │ 14   │ 15   │
    │ Brain│Agents│Memory│ Shell│Autom.│ Voice│Vision│
    └──────┴──────┴──────┴──────┴──────┴──────┴──────┘
          │
    ┌──────┴──────┐
    │ 16. ArcanisUI│
    └──────────────┘

DATA LAYER
    ┌──────────┬──────────────────┐
    │ 07.      │ 08.              │
    │ Database │ Knowledge Graph  │
    └──────────┴──────────────────┘

DEVELOPER LAYER
    ┌──────┬──────┬──────┬──────┬──────┬──────┐
    │ 01   │ 02   │ 03   │ 04   │ 05   │ 06   │
    │ Lang │Compiler│ VM  │ IDE  │ Build│ Pkg  │
    └──────┴──────┴──────┴──────┴──────┴──────┘

FOUNDATION LAYER
    ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
    │ 00  Doc  │ 24 Shared│ 25 Dev   │ 26 Test  │ 27 Exp   │ 28 Res   │ 29 Assets│
    │          │ Libs     │ Tools    │ Framework│          │          │          │
    └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                          │ 30 Scripts │
                          └────────────┘
```

## Layer Descriptions

### Foundation Layer (00, 24-30)
Cross-cutting concerns: documentation, reusable libraries, developer tooling, testing infrastructure, experimental projects, research, shared assets, and build/deployment scripts.

### Developer Layer (01-06)
The core development toolchain: the ArcanisLang programming language, its compiler, virtual machine, IDE, build system, and package manager.

### Data Layer (07-08)
Storage and knowledge: an AI-optimized database and a graph-based knowledge relationship system.

### Framework Layer (09-16)
AI and interaction frameworks: the central AI brain, multi-agent system, memory, shell, automation, voice, vision, and UI framework.

### System Layer (17-22)
Operating system primitives: desktop environment, kernel, drivers, filesystem, networking, and security.

### Application Layer (23)
ArcanisOS — the complete, integrated operating system.

## Dependency Graph

```
01 ArcanisLang → 02 ArcanisCompiler → 03 ArcanisVM
                                                     \
01 ArcanisLang → 02 ArcanisCompiler → 04 ArcanisIDE
01 ArcanisLang → 05 ArcanisBuild → 06 ArcanisPackageManager

07 ArcanisDatabase → 08 ArcanisKnowledgeGraph
07 ArcanisDatabase → 09 ArcanisBrain → 10 ArcanisAgents
09 ArcanisBrain → 11 ArcanisMemory
09 ArcanisBrain → 12 ArcanisShell
09 ArcanisBrain → 13 ArcanisAutomation
09 ArcanisBrain → 14 ArcanisVoice
09 ArcanisBrain → 15 ArcanisVision

16 ArcanisUI → 17 ArcanisDesktop

18 ArcanisKernel → 19 ArcanisDrivers
18 ArcanisKernel → 20 ArcanisFileSystem
18 ArcanisKernel → 21 ArcanisNetwork
18 ArcanisKernel → 22 ArcanisSecurity

17 ArcanisDesktop + 18-22 → 23 ArcanisOS
```

## API Philosophy

Every component exposes a clean, versioned API. Internal implementations can change as long as the API contract is maintained. This allows parallel development across the ecosystem.

## Cross-Cutting Concerns

- **SharedLibraries (24)**: Common math, data structures, serialization, logging.
- **DeveloperTools (25)**: Profilers, debuggers, analyzers.
- **Testing (26)**: Test runners, fixtures, CI templates.
- **Scripts (30)**: Build scripts, environment setup, deployment.
