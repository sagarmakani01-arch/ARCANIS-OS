# Coding Guidelines

**Path:** `standards/coding-guidelines.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Language-Specific Standards

### Rust (Primary — Kernel & Systems)

- Follow the [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- Use `unsafe` only when absolutely necessary and document safety invariants
- Prefer `Result<T, E>` over panics; panics are reserved for unrecoverable states
- All public APIs must have doc comments
- Use `clippy` at `warn` level; all warnings must be addressed before merge

### C (When Required — Hardware & Boot)

- Follow [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard)
- Use static analysis (`cppcheck`, `clang-tidy`) enforced in CI
- No variable-length arrays; no dynamic allocation in kernel context
- All pointer parameters must be annotated with `_In_`, `_Out_`, or `_Inout_`
- Bounds-checked functions only (e.g., `memcpy_s`, `strncpy_s`)

### Python (Tooling & Research)

- Follow [PEP 8](https://peps.python.org/pep-0008/) with line length 100
- Type annotations required for all function signatures
- Use `mypy` at strict mode; zero type errors before merge
- Prefer dataclasses and enums over ad-hoc dictionaries

### TypeScript (Web Components & Tooling)

- Follow [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- Strict mode enabled; no `any` unless explicitly justified with a comment
- Use `tsx` for UI components where applicable

## Universal Rules

1. **No hardcoded paths, addresses, or values** — Use constants with descriptive names
2. **No magic numbers** — Every literal has a named constant
3. **No silent error swallowing** — Every error is logged, propagated, or handled explicitly
4. **No unwrapped unwraps** — `.unwrap()` is banned; `.expect("reason")` is required
5. **Function length** — Prefer <40 lines; if longer, extract helper functions
6. **File length** — Prefer <500 lines; if longer, split the module
7. **Cyclomatic complexity** — Maximum 15 per function (measured by `llvm-cov` or equivalent)

## Error Handling Pattern (Rust)

```rust
// Good: Explicit error handling with context
pub fn read_config(path: &Path) -> Result<Config, ConfigError> {
    let data = fs::read_to_string(path)
        .map_err(|e| ConfigError::Io { path: path.to_owned(), source: e })?;
    let config: Config = toml::from_str(&data)
        .map_err(|e| ConfigError::Parse { path: path.to_owned(), source: e })?;
    Ok(config)
}

// Bad: Silent unwrap
pub fn read_config(path: &Path) -> Config {
    let data = fs::read_to_string(path).unwrap();
    toml::from_str(&data).unwrap()
}
```

## Formatting

- Rust: `rustfmt` with default settings
- C: `clang-format` with LLVM style
- Python: `black` with line length 100
- TypeScript: `prettier` with default settings
- Formatting is enforced in CI; unformatted code is rejected

---

*Consistency is more important than perfection.*
