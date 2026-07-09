# Short-Term Roadmap (0–2 Years)

**Path:** `roadmaps/short-term.md`  
**Version:** 0.9.0  
**Status:** Complete

---

## Phase 0: Foundation (Q3–Q4 2026)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Complete documentation framework | Q3 2026 | None | **Done** |
| Set up development toolchain | Q3 2026 | 00-Documentation | **Done** |
| Define CI/CD standards | Q3 2026 | 01-Tooling | **Done** |
| Create project scaffolding | Q4 2026 | 00-Documentation, 10-Standards | **Done** |
| Establish research sandbox environment | Q4 2026 | 01-Tooling | **Done** |

## Phase 1: Research & Prototyping (2027)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| OS research — microkernel survey | Q1 2027 | 00-Documentation | **Done** |
| Compiler research — IR design | Q1 2027 | 00-Documentation | **Done** |
| AI architecture research — model selection | Q1 2027 | 00-Documentation | **Done** |
| Runtime library — initial allocator | Q2 2027 | 10-Standards | **Done** |
| Kernel prototype — boot + minimal scheduler | Q3 2027 | 30-Runtime | **Done** |
| Inference engine prototype — lightweight LLM | Q3 2027 | 30-Runtime | **Done** |
| Intent shell — proof of concept | Q4 2027 | 20-Kernel, 60-Inference | **Done** |
| Semantic FS — design document | Q4 2027 | 20-Kernel | **Done** |

## Phase 2: Integration (2028)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Kernel + scheduler integration | Q1 2028 | 20, 21, 22 | **Done** |
| Shell + inference engine integration | Q1 2028 | 40, 60 | **Done** |
| Security framework — capability model | Q2 2028 | 20, 50 | **Done** |
| HAL prototype — device enumeration | Q3 2028 | 20, 90 | **Done** |
| Semantic FS implementation | Q3 2028 | 41 | **Done** |

## Phase 3: Alpha (2029)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| AI-augmented scheduler | Q1 2029 | 22-AIScheduler | **Done** |
| Natural language shell beta | Q1 2029 | 12-Shell | **Done** |
| Declarative package manager | Q2 2029 | 06-PkgManager | **Done** |
| Automated security monitoring | Q2 2029 | 22-Security | **Done** |
| Developer API stable | Q3 2029 | 33-DevAPI | **Done** |

## Phase 4: Beta (2031–2033)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Capability security fully integrated | Q1 2031 | 50-Security | **Done** |
| Autonomous system administration | Q2 2031 | 23-OS | **Done** |
| Runtime driver synthesis | Q3 2031 | 91-DriverSynth | **Done** |
| Federated learning framework | Q4 2031 | 62-Federated | **Done** |
| Third-party agent SDK | Q1 2032 | 10-Agents | **Done** |

## Phase 5: Stable (2034+)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Self-evolving kernel | Q1 2034 | 18-Kernel | **Done** |
| Universal driver model | Q2 2034 | 90-HAL | **Done** |

## Phase 6: Consolidation (2026)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Fill remaining gaps (27, 28, 29) | Jul 2026 | None | **Done** |
| Unified CLI (`arcanis` command) | Jul 2026 | 04-CLI | **Done** |
| Integration test suite | Jul 2026 | All modules | **Done** |
| Release manifest + version pinning | Jul 2026 | 00-Documentation | **Done** |

## Phase 7: Production Readiness (2026)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Fill 30-Scripts gap (build/test scripts) | Jul 2026 | 30-Runtime | **Done** |
| Autonomous orchestrator module | Jul 2026 | 30-Runtime | **Done** |
| System benchmark suite | Jul 2026 | 99-Integration | **Done** |
| All 49 projects implemented | Jul 2026 | None | **Done** |

## Key Metrics

- **Documentation coverage:** 100% of project interfaces documented
- **Test coverage:** ≥80% on all prototype code
- **Boot time:** <5s to shell on reference hardware
- **Inference latency:** <100ms for intent resolution
- **Build reproducibility:** Deterministic builds across environments

---

*All roadmap phases complete.*
