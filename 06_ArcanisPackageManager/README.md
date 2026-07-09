# Arcanis Package Manager

Manage libraries, applications, AI skills, and system modules with a unified package management system.

## Features

### Package Handling
- **Install** -- Download and install packages with dependency resolution
- **Remove** -- Uninstall packages and clean up
- **Update** -- Upgrade packages to newer versions
- **Dependency Resolution** -- Smart semver-based dependency resolution with conflict detection
- **Version Management** -- Full semver support (exact, caret `^`, tilde `~`, ranges)

### Security
- **Package Verification** -- Cryptographic signature verification and SHA-256 checksum validation
- **Permission System** -- Granular runtime permission control (network, filesystem, process, env, device)
- **Malware Scanning** -- Static analysis with severity-graded security rules
- **Trusted Sources** -- Registry authentication and trust verification via `.well-known/arcanis.txt`

### Developer Features
- **Publishing** -- Package publishing with manifest validation
- **Lock Files** -- Automatic `.arcanis/lock.json` generation for reproducible installs
- **Configuration** -- Per-project config in `.arcanis/config.json`
- **Registry API** -- RESTful registry communication with fallback support

## Quick Start

```bash
# Install a package
arcanis install @arcanis/core

# Install a specific version
arcanis install lodash ^4.17.0

# List installed packages
arcanis list

# Update a package
arcanis update @arcanis/core

# Remove a package
arcanis remove @arcanis/core

# Search registry
arcanis search "ai skill"

# Verify package integrity
arcanis verify @arcanis/core

# Publish a package
arcanis publish ./my-package

# Configure settings
arcanis config security.strictMode true
```

## Package Format

Every Arcanis package requires an `arcanis.json` manifest:

```json
{
  "name": "@scope/my-package",
  "version": "1.0.0",
  "description": "Description of your package",
  "main": "index.js",
  "dependencies": {
    "@arcanis/utils": "^1.0.0"
  },
  "permissions": ["filesystem"]
}
```

See [Package Format Spec](spec/package-format.md) for details.

## Architecture

```
src/
  cli/              CLI entry point and commands
    arcanis.js      CLI dispatcher
    commands/       install, remove, update, publish, search, verify
  core/             Core engine
    PackageManager.js      Main orchestrator
    DependencyResolver.js  Semver dependency resolution
    RegistryClient.js      Registry HTTP communication
    PackageInstaller.js    Package installation/removal
    ManifestValidator.js   Manifest schema validation
  security/         Security modules
    PackageVerifier.js     Signature and checksum verification
    MalwareScanner.js      Static code analysis
    PermissionManager.js   Runtime permission control
    TrustedSourceManager.js Registry trust management
  util/             Utilities
    logger.js       Structured logging
    fileUtils.js    Filesystem operations
```

## Configuration

Configuration is stored in `.arcanis/config.json`:

```json
{
  "registry": {
    "default": "https://registry.arcanis.dev/v1",
    "fallback": ["https://registry-backup.arcanis.dev/v1"]
  },
  "trustedSources": ["https://registry.arcanis.dev"],
  "permissions": {
    "defaultPolicy": "ask",
    "allowedScopes": ["@arcanis"]
  },
  "security": {
    "verifySignatures": true,
    "scanOnInstall": true,
    "strictMode": false
  }
}
```

## Security Model

Four-layer defense-in-depth:

1. **Signature Verification** -- RSA/ECDSA signatures on manifests, SHA-256 checksums on files
2. **Malware Scanning** -- Static analysis with critical/high/medium/low severity rules
3. **Permission System** -- Allow/deny/ask policies for network, filesystem, process, env, device
4. **Trusted Sources** -- Only verified registries can publish or supply packages

## Development

```bash
# Install dependencies
npm install

# Link CLI globally
npm link

# Run a command
arcanis --help
```

## Specification Documents

- [Package Format](spec/package-format.md) -- Manifest schema, version constraints, directory structure
- [Registry API](spec/registry-api.md) -- REST endpoints, authentication, error handling
- [Security Model](spec/security-model.md) -- Signing, scanning, permissions, trusted sources

## License

MIT
