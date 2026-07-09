# Repository Structure

**Path:** `standards/repository-structure.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Standard Project Layout

Every Arcanis project repository follows this structure:

```
arcanis-<project-name>/
├── .github/
│   ├── workflows/          # CI/CD pipeline definitions
│   │   ├── build.yml
│   │   ├── test.yml
│   │   ├── lint.yml
│   │   └── release.yml
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── README.md           # Project-specific documentation
│   ├── architecture.md     # Project architecture decisions
│   └── api.md              # API reference
├── src/
│   ├── lib.rs              # Crate root (Rust) / main module
│   ├── main.rs             # Binary entry point (if applicable)
│   └── <modules>/          # Module directories
│       ├── mod.rs
│       └── tests.rs        # Unit tests
├── tests/                  # Integration tests
│   └── integration_test.rs
├── benches/                # Benchmarks (if applicable)
│   └── bench.rs
├── examples/               # Example code
│   └── basic_usage.rs
├── scripts/                # Build and utility scripts
│   ├── build.sh
│   ├── test.sh
│   └── lint.sh
├── config/                 # Default configuration files
│   └── default.toml
├── .gitignore
├── Cargo.toml              # Rust project manifest
├── LICENSE
└── README.md               # Repository root README
```

## README Template

Every repository README must include:

```markdown
# arcanis-<project-name>

**Layer:** <0-5>  
**Status:** Research | Pre-Alpha | Alpha | Beta | Stable  
**Project ID:** XX-name  

Brief description (1–2 sentences).

## Dependencies

- arcanis-<dependency> (version requirement)
- arcanis-<dependency> (version requirement)

## Quick Start

[Build and run instructions]

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)

## Contributing

See [standards/](../standards/) in the documentation repository.
```

## Workspace Structure (Monorepo)

For projects that share a codebase:

```
arcanis-<workspace>/
├── Cargo.toml              # Workspace manifest
├── crates/
│   ├── crate-a/
│   │   ├── Cargo.toml
│   │   └── src/
│   └── crate-b/
│       ├── Cargo.toml
│       └── src/
├── tests/
├── scripts/
└── docs/
```

## Root Monorepo (Future)

When a single repository hosts multiple Arcanis projects:

```
arcanis/
├── projects/
│   ├── 20-kernel/
│   ├── 40-shell/
│   ├── 60-inference/
│   └── ...
├── docs/                   # Unified documentation
├── scripts/                # Cross-project scripts
├── Cargo.toml              # Workspace root
└── README.md
```

---

*Structure enables scale. Consistent structure enables understanding.*
