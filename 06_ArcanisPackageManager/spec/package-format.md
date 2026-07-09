# Arcanis Package Format Specification

Version 1.0.0

## Overview

An Arcanis package is a directory containing an `arcanis.json` manifest file and the package source code. Packages can be published to a registry and installed via the Arcanis Package Manager CLI.

## Manifest (`arcanis.json`)

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Package name. Scoped: `@scope/name`, unscoped: `name`. Lowercase, hyphens only. |
| `version` | String | Semver version (`major.minor.patch`) |
| `description` | String | Human-readable description |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | String | Author name or `name <email>` |
| `license` | String | SPDX license identifier |
| `main` | String | Entry point file (default: `index.js`) |
| `type` | String | Module type: `module` (ESM) or `commonjs` (default) |
| `dependencies` | Object | Map of package name to version constraint |
| `devDependencies` | Object | Development-only dependencies |
| `scripts` | Object | Lifecycle scripts |
| `permissions` | Array | Requested runtime permissions |
| `repository` | Object | `{ type, url }` |
| `keywords` | Array | Search keywords |
| `engines` | Object | Required engine versions |
| `arcanis` | Object | Arcanis-specific configuration |
| `signature` | Object | Cryptographic signature |
| `checksums` | Object | File integrity hashes (SHA-256) |

### Example Manifest

```json
{
  "name": "@arcanis/core",
  "version": "1.0.0",
  "description": "Core Arcanis runtime library",
  "main": "index.js",
  "type": "module",
  "author": "Arcanis Labs",
  "license": "MIT",
  "dependencies": {
    "@arcanis/utils": "^1.0.0",
    "fast-json": "~2.1.0"
  },
  "permissions": ["filesystem", "network"],
  "keywords": ["arcanis", "core", "runtime"],
  "repository": {
    "type": "git",
    "url": "https://github.com/arcanis/core"
  },
  "checksums": {
    "index.js": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```

## Version Constraints

| Constraint | Example | Meaning |
|------------|---------|---------|
| Exact | `1.2.3` | Only version 1.2.3 |
| Caret | `^1.2.3` | >=1.2.3, <2.0.0 |
| Tilde | `~1.2.3` | >=1.2.3, <1.3.0 |
| >= | `>=1.2.3` | >=1.2.3 |
| <= | `<=1.2.3` | <=1.2.3 |
| Any | `*` | Any version (fetches latest) |

## Package Directory Structure

```
my-package/
  arcanis.json        # Package manifest
  index.js            # Entry point
  lib/                # Module code
    module.js
  dist/               # Compiled/bundled output
    bundle.js
  README.md           # Package documentation
  LICENSE             # License file
```

## Scoped Packages

Scoped packages are prefixed with `@scope/` and are namespaced under that scope:

- `@arcanis/core` - Official Arcanis core library
- `@arcanis/utils` - Official Arcanis utilities
- `@mycompany/toolkit` - Third-party scoped package

## Publishing Requirements

1. Valid `arcanis.json` with all required fields
2. Entry point file must exist
3. Name must not conflict with existing package
4. Version must be unique for the package
5. Package must be signed (recommended)
6. Registry must be a trusted source
