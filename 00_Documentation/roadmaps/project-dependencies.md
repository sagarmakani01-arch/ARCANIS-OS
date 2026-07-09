# Project Dependencies — Milestone Map

**Path:** `roadmaps/project-dependencies.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Dependency Graph by Phase

```mermaid
graph TD
    subgraph Phase0["Phase 0: Foundation"]
        A[00 Documentation] --> B[01 Dev Tooling]
        A --> C[10 Standards]
        B --> D[02 Build System]
    end

    subgraph Phase1["Phase 1: Research"]
        C --> E[30 Runtime Library]
        D --> E
        E --> F[20 Microkernel Proto]
        E --> G[60 Inference Proto]
        F --> H[22 Scheduler Proto]
        F --> I[21 Memory Proto]
        G --> J[40 Intent Shell Proto]
        F --> J
    end

    subgraph Phase2["Phase 2: Integration"]
        F --> K[20 Kernel Full]
        H --> K
        I --> K
        G --> L[60 Inference Full]
        J --> M[40 Shell Full]
        K --> M
        L --> M
        K --> N[41 Semantic FS Design]
        K --> O[50 Security Framework]
        K --> P[90 HAL Proto]
    end

    subgraph Phase3["Phase 3: Alpha"]
        K --> Q[20 Kernel Self-Hosting]
        M --> R[40 Shell Beta]
        L --> R
        N --> S[41 Semantic FS Beta]
        O --> T[50 Security Full]
        P --> U[90 HAL Beta]
        Q --> V[02 Build System Self-Hosting]
    end

    subgraph Phase4["Phase 4: Beta"]
        Q --> W[20 Kernel AI-Augmented]
        R --> X[40 Shell Stable]
        S --> Y[41 Semantic FS Full]
        T --> Z[50 Security Autonomous]
        U --> AA[91 Driver Synthesis]
        W --> AB[22 AI Scheduler]
    end

    subgraph Phase5["Phase 5: Stable"]
        W --> AC[20 Kernel Production]
        AB --> AC
        X --> AD[40 Shell GA]
        Y --> AE[41 Semantic FS GA]
        AA --> AF[90 HAL Full]
        AC --> AG[Full Ecosystem GA]
        AD --> AG
        AE --> AG
    end
```

## Critical Path

The critical path to a functional system is:

```
00-Docs → 10-Standards → 30-Runtime → 20-Kernel → 40-Shell → Integration
                                                     60-Inference → 40-Shell
```

A delay in **30-Runtime** or **20-Kernel** will delay all downstream projects.

## Parallel Workstreams

These workstreams can proceed in parallel:

| Workstream | Projects | Lead Time |
|---|---|---|
| Kernel & Systems | 20, 21, 22, 30, 41 | 3–4 years |
| AI & Intelligence | 60, 61, 62, 70 | 2–3 years |
| Interface & Shell | 40, 80, 81 | 2–3 years |
| Hardware & Drivers | 90, 91 | 3–4 years |
| Security | 50 | 2–3 years |

## Dependency Verification

Before starting any project phase:

1. Confirm all declared dependencies are in **Active** or **Beta** status
2. Verify dependency API contracts are at least **Experimental** stability
3. Run the compatibility test suite from each dependency
4. Document any version pinning or workarounds

---

*Dependencies are not just technical — they are scheduling commitments.*
