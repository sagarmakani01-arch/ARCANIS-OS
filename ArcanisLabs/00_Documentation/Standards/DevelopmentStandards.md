# ArcanisLabs Development Standards

## Code Quality

### General Principles
- Every component must have a **single responsibility**.
- Public APIs must be **documented** and **versioned**.
- Internal implementation details must be **encapsulated**.
- Code must be **readable** first, **clever** second.

### Naming Conventions
- **Projects**: PascalCase (ArcanisLang, ArcanisVM)
- **Directories**: kebab-case (arcanis-compiler) or PascalCase per project convention
- **Files**: Match the language convention (snake_case for Rust/Python, camelCase for JS/TS)
- **Classes**: PascalCase
- **Functions/Methods**: camelCase or snake_case per language convention
- **Variables**: camelCase or snake_case per language convention
- **Constants**: UPPER_SNAKE_CASE
- **Interfaces/Traits**: Prefix with `I` or use PascalCase per language convention

### File Structure
Each project follows this layout:
```
project-name/
├── src/           # Source code
├── tests/         # Tests
├── examples/      # Usage examples (optional)
├── docs/          # Documentation
├── README.md      # Project readme
└── .gitignore     # Ignore rules
```

### Documentation Standards
Every README must include:
1. **Project name and description** — What it is and why it exists.
2. **Architecture overview** — High-level design.
3. **Setup instructions** — How to build and run.
4. **Usage examples** — Quick-start code.
5. **Development notes** — How to contribute.
6. **Dependencies** — What it depends on.

### Testing Requirements
- **Unit tests**: Cover all public API functions.
- **Integration tests**: Cover inter-component interactions.
- **Edge cases**: Empty inputs, error conditions, boundary values.
- **Test naming**: `test_<function>_<scenario>` or similar descriptive naming.

### Error Handling
- Use **explicit error types**, not generic codes.
- Errors must be **descriptive** and **actionable**.
- Never **silently swallow** errors.
- Log errors with **context** (what was happening, what failed).

### Security Practices
- Never hardcode **secrets, keys, or credentials**.
- Validate all **inputs** at boundaries.
- Follow **least privilege** for permissions.
- Use **constant-time comparisons** for sensitive data.
- Keep dependencies **updated** and **audited**.

## Version Control

### Commit Messages
```
<type>(<scope>): <description>

<body> (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

### Branch Strategy
- `main` — Stable, release-ready
- `develop` — Integration branch
- `feature/<name>` — New features
- `fix/<name>` — Bug fixes
- `experiment/<name>` — Experimental work

## Inter-Project Communication

### API Contracts
- APIs must be defined in a **language-agnostic format** (protobuf, OpenAPI, or plain interface definition).
- Breaking changes require a **major version bump**.
- Deprecated APIs must be maintained for **one minor version** before removal.

### Dependency Management
- Projects may depend on **earlier-numbered projects only** (no circular dependencies).
- Dependencies must be **explicitly declared** in project documentation.
- When a dependency changes its API, all dependents must be **updated and tested**.

## AI-First Development

### Integration Points
- Every project should identify **where AI can enhance** its functionality.
- AI components must have **fallback modes** when models are unavailable.
- AI interactions should be **logged** for debugging and improvement.

### Model Governance
- Models must be **versioned** alongside code.
- Training data provenance must be **documented**.
- Bias testing is **required** for user-facing AI features.

## Environment Setup

### Required Tools
- Git for version control
- Language-specific toolchains (Rust, Python, Node.js as needed)
- Docker for containerized development (optional)

### Development Workflow
1. Read the project's README and docs.
2. Set up the development environment.
3. Run existing tests to verify setup.
4. Create a feature branch.
5. Write tests first (TDD recommended).
6. Implement the feature.
7. Run all tests.
8. Submit a pull request.
