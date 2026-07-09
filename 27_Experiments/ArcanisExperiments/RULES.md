# Rules

These rules keep ArcanisExperiments a **safe** sandbox.

## 1. Experimental code only
- Everything here is speculative. Nothing here is production.
- No stable/shared code may be modified from this workspace.

## 2. Do not affect stable projects
- Never edit files outside `ArcanisExperiments/`.
- Do not install global dependencies that other projects rely on.
- Prefer isolated virtual environments, containers, or sandboxes.
- If an experiment risks side effects, isolate it (VM, container, branch).

## 3. Maintain documentation
- Every experiment starts from a `templates/` scaffold.
- Keep the front-matter `status` and `Log` up to date.
- Research notes go in `research-notes/`.
- Archive finished work rather than deleting it.

## 4. Safety
- No destructive commands against host systems.
- Hardware experiments must note required safety precautions.
- Kernel experiments must run in a VM unless explicitly cleared.

## 5. Hygiene
- Commit freely; this repo is for exploration.
- Clean up large artifacts or move them to external storage.
