# Research: Programming Languages

**Path:** `research/programming-languages.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Language Selection Rationale

### Rust (Primary — Kernel, Systems, Tools)
**Why:** Memory safety without GC, zero-cost abstractions, FFI, growing ecosystem, excellent concurrency support.
- Kernel: `arcanis-kernel` — No `std`, `no_std` environment, custom allocators
- Systems: `arcanis-scheduler`, `arcanis-memory`, `arcanis-net` — Full `std`, async
- Tools: Build system, CLI utilities

### C (When Required — Boot, Hardware, Firmware)
**Why:** Universal compatibility, existing hardware interfaces, boot protocols.
- Bootloader: UEFI, Multiboot
- Firmware: Device initialization
- FFI boundary: C ABI for hardware interaction
- **Used only where Rust cannot be used.**

### Python (Research, Tooling, ML)
**Why:** Rapid prototyping, ML ecosystem, scripting.
- Research: Prototype algorithms before porting to Rust
- ML: Model training, data pipelines
- Tooling: Build scripts, code generation, automation
- **Never used in the kernel or performance-critical paths.**

### TypeScript / JavaScript (Web Components, Interface)
**Why:** Ubiquitous for web-based and Electron-like interfaces.
- Developer tooling UI
- Web-based system monitors
- Documentation site
- **Used only for non-critical user-facing interfaces.**

## Research Languages (Under Evaluation)

| Language | Potential Use Case | Concerns |
|---|---|---|
| **Zig** | Bootloader, low-level tooling | Ecosystem maturity, tooling |
| **Go** | Network services, CLI tools | GC latency, runtime size |
| **Crystal** | System scripting | Maturity, ecosystem |
| **OCaml** | Formal verification, compiler | Learning curve, ecosystem |
| **Haskell** | Protocol specification | Performance predictability |

## Language Features We Need

1. **Memory safety** — No buffer overflows, use-after-free, or double-free
2. **Zero-cost abstractions** — No hidden allocation or runtime overhead
3. **Deterministic destruction** — RAII or equivalent
4. **Concurrency without data races** — Ownership model or equivalent
5. **FFI** — Must interoperate with C for hardware access
6. **Cross-compilation** — Must target multiple architectures from a single toolchain
7. **Minimal runtime** — Kernel cannot depend on a GC or large runtime

## Internal DSL Strategy

For the Arcanis build system and configuration, we will develop internal DSLs:

- **Build DSL** (Rust macros) — Declarative build definitions
- **Policy DSL** (Rust macros or TOML) — Security capability declarations
- **Hardware DSL** (YAML or TOML) — Device capability descriptions (for driver synthesis)

---

*Choose languages for their strengths. Design interfaces for interoperability.*
