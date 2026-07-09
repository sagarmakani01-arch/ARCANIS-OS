# Dependency Relationships

**Path:** `architecture/dependencies.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Dependency Graph Rules

1. **No circular dependencies** — Project A cannot depend on B if B (transitively) depends on A
2. **Layer constraints** — Projects may only depend on projects in the same or lower layer
3. **Explicit declarations** — All dependencies are declared in a `dependencies.toml` per project
4. **Minimum dependency principle** — A project must not depend on another project for a single function

## Dependency Map

```
00 Documentation  ─────────────────────────────────────────────────────────┐
01 Tooling        ──▶ 00                                                  │
02 Build System   ──▶ 01                                                  │
10 Standards      ──▶ 00                                                  │
                                                                          │
20 Microkernel    ──▶ 10, 30                                              │
21 Memory Manager ──▶ 20, 30                                              │
22 Scheduler      ──▶ 20, 30                                              │
30 Runtime Library────────────────────────────────────────────────────────┤
                                                                          │
40 Intent Shell   ──▶ 20, 30, 41, 60, 80                                 │
41 Semantic FS    ──▶ 20, 30                                              │
42 Network Stack  ──▶ 20, 30                                              │
50 Security       ──▶ 20, 30, 60                                          │
                                                                          │
60 Inference Eng  ──▶ 30                                                  │
61 Policy & Plan  ──▶ 30, 60                                              │
62 Federated      ──▶ 30, 60                                              │
70 User Modeling  ──▶ 30, 60, 61                                          │
                                                                          │
80 NL Interface   ──▶ 30, 60, 70                                          │
81 Accessibility  ──▶ 30, 80                                              │
                                                                          │
90 HAL            ──▶ 20                                                  │
91 Driver Synth   ──▶ 30, 60, 90                                          │
```

## Dependency Types

| Type | Description | Example |
|---|---|---|
| **Build** | Required to compile | Compiler, code generation |
| **Link** | Required at link time | Runtime library, kernel API |
| **Runtime** | Required at execution | Scheduler, inference engine |
| **Test** | Required only for testing | Test frameworks, simulators |
| **Optional** | Enhances functionality but not required | Hardware acceleration |

## Version Compatibility

- Dependencies are specified with semver ranges (e.g., `>=1.2.0 <2.0.0`)
- Breaking changes in a dependency require a MAJOR version bump in the dependent project
- A compatibility matrix is maintained at `architecture/compatibility-matrix.json` (future)

## Dependency Resolution

The build system resolves dependencies using:
1. **Exact version** from the project manifest if specified
2. **Workspace resolution** — shared dependency graph across all projects
3. **Override mechanism** — for testing and development, specific versions can be pinned

---

*Dependencies are liabilities. Every dependency must earn its place.*
