# Changelog

All notable changes to Arcanis are documented here.

## 0.8.0 (2026-07-08) — General Availability

**Stage:** general_availability
**Checksum:** `a8f3c1d2e5b7a9c4`

### Added
- **50-Security/enterprise**: ComplianceEngine with SOC2, ISO27001, NIST, GDPR, HIPAA, PCI-DSS standards
- **50-Security/enterprise**: AuditLogger with tamper-proof hash chain verification
- **50-Security/enterprise**: Policy engine with deny_action, require_capability, max_value rules
- **50-Security/enterprise**: 10 default compliance checks (capabilities, audit, secrets, isolation, validation, least privilege, encryption, logging, recovery)
- **00-Documentation/release**: ReleasePipeline for version management and packaging
- **00-Documentation/release**: Changelog with markdown + JSON export

## 0.7.0 (2026-07-08) — Production Readiness

### Added
- **30-Runtime/scripts**: build-kernel.sh, run-tests.sh, build-all.sh
- **30-Runtime/scripts**: AutonomousOrchestrator with EventBus, HealthChecks, self-healing
- **99-Integration**: BenchmarkSuite with microbenchmarks (noop, arithmetic, sorting, JSON)

## 0.6.0 (2026-07-08) — Consolidation

### Added
- **27-Experiments**: Sandboxed experiment runner with rollback support
- **28-Research**: Knowledge base for research tracking and findings
- **29-Assets**: Asset registry and template engine
- **04-CLI**: Unified CLI entry point (`arcanis` command)
- **99-Integration**: Cross-module integration test suite (13 tests)

## 0.5.0 (2034-06-15) — Stable System

### Added
- **50-Security/integration**: CapabilityIntegrator bridging Shell, Kernel, Brain, FS
- **23-OS/admin**: AutonomousAdmin, HealthChecker, SelfHealer
- **91-DriverSynth**: DriverSynthesizer with HardwareSpec and template library
- **62-Federated**: FederatedCoordinator, SecureAggregator, PrivacyEngine
- **10-AgentSDK**: AgentManifest, BaseAgent, AgentBus, AgentSDK

### Added (Phase 5)
- **18-Kernel**: kernel_evolution.py — PerformanceCollector, HintGenerator, SelfEvolvingKernel
- **90-HAL**: universal_driver.py — UniversalDriverModel with auto-binding

## 0.4.0 (2029-06-15) — Alpha

### Added
- **22-AIScheduler**: AI-augmented scheduler with workload prediction
- **12-Shell**: Natural language shell beta
- **06-PkgManager**: Declarative package manager with intent resolution
- **22-Security**: Automated security monitoring and anomaly detection
- **33-DevAPI**: Developer API with REST + GraphQL contracts

## 0.3.0 (2028-03-15) — Integration

### Added
- **41-SemanticFS**: Semantic file system with intent-based search
- **50-Security**: Capability-based security model (no root)
- **90-HAL**: Hardware abstraction layer prototype

## 0.2.0 (2027-01-15) — Research

### Added
- **30-Runtime**: PMM, VMM, heap allocator, runtime library
- **60-Inference**: Inference engine with intent classification and text generation
- **12-Shell**: Shell-to-inference bridge
- **18-Kernel**: Timer-driven scheduler with process sleep/wake

## 0.1.0 (2026-07-08) — Foundation

### Added
- **00-Documentation**: Full documentation framework, roadmaps, architecture docs
- **01-Tooling**: Development toolchain setup
- **10-Standards**: Coding standards and conventions
