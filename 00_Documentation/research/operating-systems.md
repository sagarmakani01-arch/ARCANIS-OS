# Research: Operating Systems

**Path:** `research/operating-systems.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Areas of Study

### Microkernel Architecture
- **L4 / seL4** — Formal verification, minimal trusted computing base, capability-based IPC
- **MINIX 3** — Reliability through microkernel design, driver isolation
- **QNX** — Real-time microkernel, adaptive partitioning
- **Google Fuchsia** — Zircon kernel, capability-based, modern IPC (Zircon channels)

### Monolithic Kernel (for comparison)
- **Linux** — CFS scheduler, VFS, memory management, extensive driver ecosystem
- **FreeBSD** — ZFS, DTrace, jail isolation

### Unikernels & Specialized
- **MirageOS** — OCaml unikernel, type-safe, minimal
- **IncludeOS** — C++ unikernel, minimal boot time
- **OSv** — Cloud-optimized, Java/Node.js workloads

### Research Kernels
- **Plan 9** — Distributed, per-process namespaces, 9P protocol
- **Inferno** — Dis VM, Styx protocol, portable
- **HelenOS** — Multiserver microkernel, driver in user space
- **Tock** — Rust-based, memory-safe, for embedded systems

## Key Takeaways for Arcanis

### Adopt
- **seL4-style formal verification** for the trusted computing base
- **Capability-based IPC** as the universal communication primitive
- **User-space drivers** (MINIX/QNX model) for stability
- **Per-process namespaces** (Plan 9) for flexibility
- **Rust-based kernel** (Tock) for memory safety

### Avoid
- Monolithic kernel complexity — Linux is too large to formally verify
- Overly restrictive hardware compatibility — must support common hardware
- Single-language lock-in — the kernel is Rust, but user-space supports multiple languages

## Open Questions

1. Can seL4's formal verification be extended to an AI-augmented scheduler?
2. What is the minimum latency for capability-based IPC vs. traditional syscalls?
3. Can a Plan 9-style namespace model work with capability security?
4. How do we bootstrap the system without AI (recovery mode)?

## References

- [seL4: Formal Verification of an OS Kernel](https://sel4.systems/)
- [The MINIX 3 Operating System](https://www.minix3.org/)
- [Plan 9 from Bell Labs](https://9p.io/plan9/)
- [Tock Embedded OS](https://www.tockos.org/)

---

*Study history. Build the future.*
