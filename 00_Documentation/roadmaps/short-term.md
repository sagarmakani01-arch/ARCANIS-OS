# Short-Term Roadmap (0–2 Years)

**Path:** `roadmaps/short-term.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Phase 0: Foundation (Current — Q4 2026)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Complete documentation framework | Q3 2026 | None | **Active** |
| Set up development toolchain | Q3 2026 | 00-Documentation | Planned |
| Define CI/CD standards | Q3 2026 | 01-Tooling | Planned |
| Create project scaffolding | Q4 2026 | 00-Documentation, 10-Standards | Planned |
| Establish research sandbox environment | Q4 2026 | 01-Tooling | Planned |

## Phase 1: Research & Prototyping (2027)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| OS research — microkernel survey | Q1 2027 | 00-Documentation | Planned |
| Compiler research — IR design | Q1 2027 | 00-Documentation | Planned |
| AI architecture research — model selection | Q1 2027 | 00-Documentation | Planned |
| Runtime library — initial allocator | Q2 2027 | 10-Standards | Planned |
| Kernel prototype — boot + minimal scheduler | Q3 2027 | 30-Runtime | Planned |
| Inference engine prototype — lightweight LLM | Q3 2027 | 30-Runtime | Planned |
| Intent shell — proof of concept | Q4 2027 | 20-Kernel, 60-Inference | Planned |
| Semantic FS — design document | Q4 2027 | 20-Kernel | Planned |

## Phase 2: Integration (2028)

| Milestone | Target | Dependencies | Status |
|---|---|---|---|
| Kernel + scheduler integration | Q1 2028 | 20, 21, 22 | Planned |
| Shell + inference engine integration | Q1 2028 | 40, 60 | Planned |
| System can boot and run simple commands via NL | Q2 2028 | 20, 40, 60 | Planned |
| Security framework — capability model prototype | Q2 2028 | 20, 50 | Planned |
| HAL prototype — basic device enumeration | Q3 2028 | 20, 90 | Planned |
| First developer preview release | Q4 2028 | All above | Planned |

## Key Metrics

- **Documentation coverage:** 100% of project interfaces documented
- **Test coverage:** ≥80% on all prototype code
- **Boot time:** <5s to shell on reference hardware
- **Inference latency:** <100ms for intent resolution
- **Build reproducibility:** Deterministic builds across environments

---

*Short-term milestones are commitments. Long-term milestones are directions.*
