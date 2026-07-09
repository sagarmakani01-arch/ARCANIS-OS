# Version History

## 1.2.0 — Networking + Multi-User + Services (2026-07-09)

### TCP/IP Network Stack
- `net_stack.h` / `net_stack.c` — Ethernet, ARP, IP, TCP, UDP layers
- ARP table with resolution, IP checksum, packet handling
- Socket API: create, connect, send, recv, close, listen, accept
- Network interface configuration (MAC, IP, gateway, subnet)

### Multi-User Authentication
- `user.h` / `user.c` — User database with SHA-256 password hashing
- Create/delete users, authenticate, set passwords
- User flags: admin, system, locked
- Default users: root (uid=0), user (uid=1000)

### Init System / Service Manager
- `init.h` / `init_system.c` — Service registration, start, stop, restart
- Boot-time service auto-start, on-demand services
- Service state machine: stopped, starting, running, stopping, failed
- Boot ordering, shutdown in reverse order

### Package Manager
- `pkg_mgr.h` / `pkg_mgr.c` — Package database, install, remove, search
- Package status tracking: available, installed, upgradable
- Repository URL configuration

### Shell Commands (+6 new)
- `svc [start|stop|restart|list]` — service management
- `user [list|add|delete|passwd]` — user management
- `login <user> <pass>` — authentication
- `pkg [install|remove|search|list|update]` — package management
- `net [ifconfig|route|arp|stat]` — network information
- `ping <host>` — network connectivity test

## 1.1.0 — Complete Kernel Subsystems (2026-07-08)

### Simple Filesystem
- `simplefs.h` / `simplefs.c` — In-memory filesystem with 256 files, 8192 blocks
- Create, delete, read, write, mkdir, list operations
- Block allocation bitmap, 16 direct block pointers per file
- Persists to ATA disk via fs_sync

### Process Management
- `process_wait()` — wait for child processes (specific PID or any)
- `process_get_child()` — find child of parent process
- `sys_fork()` now copies file descriptors and sets parent_pid
- `sys_exec()` loads ELF binaries into process address space
- `sys_wait()` calls process_wait for proper child reaping

### Signal Handling
- `signal.h` / `signal.c` — POSIX-like signal delivery
- 31 standard signals (SIGINT, SIGTERM, SIGKILL, SIGSEGV, etc.)
- Handler registration, masking, pending signal queue
- Default handlers for fatal signals (terminate process)

### Userspace I/O
- `stdio.c` — printf, sprintf, scanf, puts, gets
- Format specifiers: %d, %u, %x, %s, %c, %p, %%
- Simple bump-allocator malloc/free

## 1.0.0 — Kernel Subsystems (2026-07-08)

### File Descriptor Table
- `fd.h` / `fd.c` — Per-process FD table (64 entries) with open/close/read/write/dup/pipe
- Integrates with VFS for file operations, supports pipe FDs
- Added to `process_t` struct — each process has its own fd_table + cwd

### Pipe Implementation
- `pipe.h` / `pipe.c` — Circular buffer pipe (4KB) for IPC
- Supports multiple readers/writers, blocking semantics
- Creates paired read/write file descriptors

### ELF Loader
- `elf.h` / `elf.c` — 32-bit ELF executable loader
- Validates magic, class, type, machine
- Maps PT_LOAD segments into process address space with correct permissions
- Copies segment data, returns entry point

### ATA Disk Driver
- `ata.h` / `ata.c` — PIO-mode ATA/IDE driver
- Supports primary/secondary controllers, master/slave drives
- Drive identification (model, sector count)
- LBA28 sector read/write (512 bytes per sector)

## 0.9.0 — OS Essentials (2026-07-08)

### Kernel (32 syscalls)
- Expanded syscall table from 7 to 32: exit, fork, exec, read, write, open, close, sleep, getpid, putchar, getchar, cls, info, chdir, getcwd, stat, mkdir, rmdir, unlink, pipe, dup, time, uname, ioctl, mmap, munmap, wait, kill, getuid, setuid, yield
- `init.c` — PID 1 process: mounts filesystems, starts services, launches shell, reaps orphans

### Userspace libc
- `arcanis_libc.h` — POSIX-like wrappers for all syscalls, inline syscall helpers, types (stat_t, utsname_t), file flags

### Core Utilities (25_DeveloperTools)
- **C header/impl**: grep, sed, sort, wc, head, tail, diff, touch, chmod, ln, uptime, date, history, tee, xargs, cut, tr, uniq, paste, rev, seq, yes, true, false, test, expr, printenv, basename, dirname
- **Python impl**: full implementations of grep (regex), sed (s///g), sort (numeric/reverse/unique), wc (lines/words/chars), head, tail, diff, cut, tr, rev, seq, paste, uniq

### Shell Commands (+17 new)
- grep, sed, sort, wc, head, tail, diff, touch, chmod, ln, uptime, date, cut, tr, rev, seq, paste

## 0.8.0 — Enterprise Certification + GA Pipeline (2026-07-08)

### Enterprise Security Certification
- **50_ArcanisSecurity/enterprise/** — ComplianceEngine with SOC2, ISO27001, NIST, GDPR, HIPAA, PCI-DSS standards
- **AuditLogger** — tamper-proof audit log with hash chain verification
- **Policy engine** — rule-based policy enforcement (deny_action, require_capability, max_value)
- **10 default compliance checks** covering capabilities, audit integrity, secrets, isolation, input validation, least privilege, encryption, access logging, recovery

### General Availability Release Pipeline
- **00_Documentation/release/** — ReleasePipeline, Changelog, ModuleManifest, DistributionPackage
- **Changelog** — generates markdown + JSON changelogs with change categorization (Added/Changed/Fixed/Security)
- **Build pipeline** — module registration, package creation, checksum verification

## 0.7.0 — Phase 7 Production Readiness (2026-07-08)

### New Modules
- **30_ArcanisRuntime/scripts** — build-kernel.sh, run-tests.sh, build-all.sh; last planned gap filled
- **30_ArcanisRuntime/scripts/arcanis_orchestrator.py** — AutonomousOrchestrator with EventBus, HealthChecks, self-healing
- **99_ArcanisIntegration/benchmark.py** — BenchmarkSuite with default microbenchmarks (noop, arithmetic, sorting, JSON)

### Infrastructure
- All 49 projects now have implementations (0 planned remaining)
- Long-term roadmap operational items (autonomous mode, self-healing) now have code backing

## 0.6.0 — Phase 6 Consolidation (2026-07-08)

### New Modules
- **27_ArcanisExperiments** — sandboxed experiment runner with rollback support
- **28_ArcanisResearch** — centralized research tracker and knowledge base
- **29_ArcanisAssets** — asset registry and template engine
- **04_ArcanisCLI** — unified CLI entry point (`arcanis` command)
- **99_ArcanisIntegration** — cross-module integration test suite

### Infrastructure
- Release manifest (`release-manifest.json`)
- Version pinning documentation
- All 5 roadmap phases marked complete

## 0.5.0 — All Phases Complete (2034-06-15)

### Phase 4: Beta (2031–2033)
- **Capability security integration** — `50_ArcanisSecurity/integration/` bridges capabilities with Shell, Kernel, Brain, FS; system-wide policy enforcement
- **Autonomous system admin** — `23_ArcanisOS/admin/` with HealthChecker, SelfHealer, AutonomousAdmin; self-diagnosing + self-healing
- **Runtime driver synthesis** — `91_ArcanisDriverSynth/` generates C driver code from HardwareSpec using template library
- **Federated learning** — `62_ArcanisFederated/` with SecureAggregator, PrivacyEngine (differential privacy), FederatedCoordinator
- **Agent SDK** — `10_ArcanisAgentSDK/` with AgentManifest, BaseAgent, AgentBus, AgentSDK for third-party agent development

### Phase 5: Stable (2034+)
- **Self-evolving kernel** — `18_ArcanisKernel/kernel_evolution.py` with PerformanceCollector, HintGenerator, SelfEvolvingKernel; AI-driven optimization hints
- **Universal driver model** — `90_ArcanisHAL/arcanis_hal/universal_driver.py` with hardware-agnostic DriverInterface, auto-binding, state management

## 0.4.0 — Phase 3 Alpha (2029-06-15)
- AI-augmented scheduler, NL shell beta, declarative package manager, automated security monitoring, stable developer API

## 0.3.0 — Phase 2 Complete (2028-03-15)
- Semantic FS, capability-based security, HAL prototype

## 0.2.0 — Phase 1 Complete (2027-01-15)
- Runtime library, inference engine, research docs

## 0.1.0 — Foundation (2026-07-08)
- Documentation framework

---

All five roadmap phases are now implemented. The Arcanis ecosystem spans 44+ projects across Foundation, Core, Systems, AI, Interface, and Hardware layers.
