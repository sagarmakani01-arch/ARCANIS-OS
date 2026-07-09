# Testing Standards

**Path:** `standards/testing-standards.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Test Levels

### 1. Unit Tests
- Test individual functions, methods, and modules in isolation
- Located at `src/<module>/tests.rs` (inline) in Rust
- Coverage target: **≥90%** of all function-level logic
- No external dependencies (no filesystem, network, or other services)
- Run with `cargo test` or language-equivalent

### 2. Integration Tests
- Test interactions between modules and projects
- Located at `tests/` directory in the repository root
- Coverage target: **≥80%** of documented interfaces
- May use test fixtures, mock services, or lightweight test harnesses
- Run with `cargo test --test <name>` or equivalent

### 3. System Tests
- Test the full system end-to-end
- Run in isolated environments (containers, VMs, or simulators)
- Coverage target: All critical user journeys and error scenarios
- Automated via CI on every merge to main

### 4. Property-Based Tests
- Use `proptest` (Rust) or `hypothesis` (Python) where applicable
- Required for: parsers, serialization, scheduling policies, memory allocators
- Run as part of the unit test suite

### 5. Fuzz Tests
- Use `cargo-fuzz` (Rust) or `afl` (C) for security-critical code
- Required for: IPC handlers, syscall dispatchers, network packet parsers
- Run nightly in CI; crashes are P0 bugs

### 6. Performance / Regression Tests
- Benchmarks track performance over time
- Located at `benches/` directory
- Run on every PR; regressions >5% block merge
- Use `criterion` (Rust) or `pytest-benchmark` (Python)

## Testing Rules

1. **Tests must be deterministic** — No flaky tests. Randomness must use seeded RNGs.
2. **Tests must be fast** — Unit tests complete in <1s; integration tests in <30s; system tests in <10m
3. **Tests must be isolated** — No test depends on the state left by another test
4. **Tests must be meaningful** — Test behavior, not implementation. Prefer black-box testing.
5. **No test is too small** — Even a one-line test for an edge case is valuable.

## CI Pipeline

```
┌─────────────┐
│   Lint      │  ← rustfmt, clippy, mypy, prettier (5m max)
└──────┬──────┘
       ▼
┌─────────────┐
│   Build     │  ← Compile all targets (10m max)
└──────┬──────┘
       ▼
┌─────────────┐
│ Unit Tests  │  ← All unit + property tests (5m max)
└──────┬──────┘
       ▼
┌─────────────┐
│ Integ. Tests│  ← All integration tests (10m max)
└──────┬──────┘
       ▼
┌─────────────┐
│  Security   │  ← cargo-audit, SAST scanning (5m max)
└──────┬──────┘
       ▼
┌─────────────┐
│   Bench     │  ← Performance regression check (5m max)
└──────┬──────┘
       ▼
    Merge OK
```

## Test Naming

```
test_<scenario>_<expected_behavior>

Examples:
- test_empty_queue_returns_none
- test_invalid_page_fault_returns_error
- test_concurrent_writes_are_consistent
```

## Coverage Reporting

- Use `tarpaulin` (Rust), `gcov` (C), `coverage.py` (Python), `c8` (TypeScript)
- Coverage reports generated on every CI run
- Coverage is a guideline, not a target for its own sake — high coverage with weak assertions is not acceptable

---

*A test suite is the executable specification of the system.*
