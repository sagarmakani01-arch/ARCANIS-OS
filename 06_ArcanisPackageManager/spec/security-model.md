# Arcanis Security Model

Version 1.0.0

## Overview

Arcanis implements a defense-in-depth security model with four layers:

1. **Package Verification** - Cryptographic integrity checks
2. **Malware Scanning** - Static analysis of package code
3. **Permission System** - Runtime capability control
4. **Trusted Sources** - Registry authentication and trust

## 1. Package Verification

### Signatures

Packages can be signed using asymmetric cryptography (RSA/ECDSA with SHA-256).

**Signing process:**
1. Package author generates a key pair
2. All package files are checksummed (SHA-256)
3. Checksums are written to manifest
4. Manifest (without signature field) is signed with private key
5. Signature value and public key are added to manifest

**Verification process:**
1. Recompute checksums of all files
2. Compare against manifest checksums
3. Verify manifest signature using embedded public key

### Checksums

```json
{
  "checksums": {
    "index.js": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "lib/util.js": "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
  }
}
```

## 2. Malware Scanning

### Static Analysis Rules

Packages are scanned at install time for suspicious patterns:

| Severity | Pattern | Example |
|----------|---------|---------|
| Critical | Command execution | `child_process.exec()`, `spawn()` |
| High | Dynamic code execution | `eval()`, `new Function()` |
| High | Dynamic require | `require(someVar + '.js')` |
| High | Obfuscation | Hex escapes, `fromCharCode` |
| Medium | Filesystem modification | `fs.writeFile()`, `fs.unlink()` |
| Medium | Process spawning | `child_process.fork()` |
| Low | Network access | `http.get()`, `fetch()` |
| Low | Environment access | `process.env` |

### Scan Levels

- **Basic** (default): Static pattern matching on package source
- **Deep**: Recursive dependency tree scanning with severity reporting
- **Strict**: Blocks installation on any high+ severity finding

### Configuration

```json
{
  "security": {
    "verifySignatures": true,
    "scanOnInstall": true,
    "strictMode": false
  }
}
```

## 3. Permission System

### Permission Policies

| Policy | Behavior |
|--------|----------|
| `allow` | Automatically grant all permissions |
| `deny` | Automatically deny all permissions |
| `ask` | Prompt user for each permission request |

### Permission Types

| Permission | Description |
|------------|-------------|
| `network` | Make HTTP/HTTPS requests |
| `filesystem` | Read/write files outside package dir |
| `process` | Spawn child processes |
| `env` | Access environment variables |
| `device` | Access hardware devices |

### Permission Requests

Packages declare required permissions in their manifest:

```json
{
  "permissions": ["filesystem", "network"]
}
```

## 4. Trusted Sources

### Built-in Trusted Sources

- `https://registry.arcanis.dev`
- `https://packages.arcanis.org`

### Source Verification

Registries must respond to `/.well-known/arcanis.txt` with content containing `arcanis-registry` to be verified.

### Configuration

```json
{
  "trustedSources": [
    "https://registry.arcanis.dev",
    "https://my-private-registry.com"
  ]
}
```

## Security Best Practices

1. **Always verify signatures** before installing packages
2. **Use strict mode** in production environments
3. **Pin dependencies** to exact versions in production
4. **Audit permissions** requested by packages
5. **Only add trusted sources** you control
6. **Run `arcanis verify`** periodically on installed packages
7. **Use scoped packages** (`@org/name`) to prevent typosquatting
