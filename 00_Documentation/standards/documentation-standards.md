# Documentation Standards

**Path:** `standards/documentation-standards.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Documentation Principles

1. **Document why, not just what** — The purpose and reasoning behind a decision is more valuable than the decision itself
2. **Write for two audiences** — Every document should be understandable by beginners and referenceable by experts
3. **Keep it close to the code** — Documentation that lives in the codebase stays accurate; documentation that lives elsewhere drifts
4. **Modularity** — Each document covers one topic. Cross-reference rather than duplicate.
5. **Version everything** — Every document has a version number and last-updated date

## Document Types

### Architecture Decision Records (ADRs)
- File: `docs/adr/NNNN-title.md`
- Purpose: Document significant architectural decisions, their context, and their consequences
- Required for: Any decision that affects cross-project interfaces, dependencies, or system behavior

### READMEs
- Every repository and every crate/module has a README
- Repository README: Project overview, quick start, links to detailed docs
- Module README: Purpose, key types, usage examples

### API Documentation
- Rust: Use `///` doc comments on all public items
- Generate with `rustdoc` and publish to project documentation site
- Include: type signatures, descriptions, examples, panic conditions, error types

### Design Documents
- File: `docs/design/<topic>.md`
- Purpose: Deep dives into specific subsystem design
- Audience: Architects and contributors
- Contains: Problem statement, design options considered, chosen approach, trade-offs

### Tutorials
- File: `docs/tutorials/<name>.md`
- Purpose: Step-by-step guides for common tasks
- Audience: New users and contributors
- Every tutorial must work end-to-end; tested in CI

## Metadata Header

Every document must start with:

```markdown
# Title

**Path:** `relative/path/from/repo/root.md`  
**Version:** 0.1.0  
**Status:** Draft | Review | Active | Superseded

---
```

Status values:
- **Draft** — Initial writing; subject to significant change
- **Review** — Under review by the team; feedback expected
- **Active** — Current and maintained
- **Superseded** — Replaced by a newer document (reference the replacement)

## Markdown Style

- Use ATX headings (`#`, `##`, etc.) — no Setext headings
- Use fenced code blocks with language tags: ```rust, ```python, ```c
- Use tables for structured comparisons
- Use bullet lists for unordered items
- Use numbered lists for sequences or priorities
- Use `>` for quotations and notes
- Use **bold** for emphasis, *italic* for technical terms
- Maximum line length: **100 characters** (wrap manually)

## Cross-Referencing

- Link to other documents using relative paths: `[name](../vision/philosophy.md)`
- Link to code with file path + line: `src/lib.rs:42`
- Link to issues: `#123`
- Link to external resources with full URLs

## Diagrams

- Use [Mermaid](https://mermaid.js.org/) for diagrams where possible
- Store as fenced code blocks with `mermaid` tag
- For complex diagrams, store in `docs/diagrams/` as SVG

## Version History

- A `VERSION.md` at the root of the documentation tracks all changes
- Each document lists its own version in the metadata header
- Significant changes to a document increment the MINOR version
- Typo fixes and clarifications increment the PATCH version

---

*Good documentation is not a luxury. It is a requirement for scale.*
