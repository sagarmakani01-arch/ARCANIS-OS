# ArcanisScripts Script Reference

Complete reference for all ArcanisScripts commands and options.

## Build Scripts

### build.ps1 / build.sh

Build automation for compiling, bundling, and packaging projects.

#### Usage

**PowerShell:**
```powershell
.\ArcanisScripts\build\build.ps1 [target] [options]
```

**Bash:**
```bash
./ArcanisScripts/build/build.sh [target] [options]
```

#### Targets

| Target | Description | Default |
|--------|-------------|---------|
| `all` | Run clean, compile, and bundle | Yes |
| `clean` | Remove build artifacts | No |
| `compile` | Compile source code | No |
| `bundle` | Create distributable archive | No |
| `docker` | Build Docker image | No |
| `help` | Show help message | No |

#### Options

| Option | PowerShell | Bash | Description |
|--------|------------|------|-------------|
| Clean before | `-Clean` | `-c, --clean` | Clean before building |
| Verbose | `-Verbose` | `-v, --verbose` | Enable verbose output |
| Force | `-Force` | `-f, --force` | Skip confirmations |
| Configuration | `-Configuration` | `-C, --config` | Debug or Release |
| Output dir | `-OutputDir` | `-o, --output` | Output directory |

#### Examples

```bash
# Full build
./ArcanisScripts/build/build.sh

# Clean build with debug configuration
./ArcanisScripts/build/build.sh compile --config Debug --clean

# Create Docker image
./ArcanisScripts/build/build.sh docker --force
```

#### Project Detection

| Project Type | Detection Method | Build Command |
|--------------|------------------|---------------|
| Node.js | `package.json` | `npm run build` |
| TypeScript | `tsconfig.json` | `npm run build` |
| Rust | `Cargo.toml` | `cargo build --release` |
| Go | `go.mod` | `go build -o dist/app` |
| .NET | `*.csproj` | `dotnet build -c Release` |

---

## Test Scripts

### test.ps1 / test.sh

Testing automation for running tests and generating reports.

#### Usage

**PowerShell:**
```powershell
.\ArcanisScripts\test\test.ps1 [action] [options]
```

**Bash:**
```bash
./ArcanisScripts/test/test.sh [action] [options]
```

#### Actions

| Action | Description | Default |
|--------|-------------|---------|
| `all` | Run unit, integration, and lint | Yes |
| `unit` | Run unit tests only | No |
| `integration` | Run integration tests only | No |
| `e2e` | Run end-to-end tests | No |
| `coverage` | Generate coverage report | No |
| `lint` | Run linter | No |
| `help` | Show help message | No |

#### Options

| Option | PowerShell | Bash | Description |
|--------|------------|------|-------------|
| Watch | `-Watch` | `-w, --watch` | Continuous testing |
| Verbose | `-Verbose` | `-v, --verbose` | Enable verbose output |
| Force | `-Force` | `-f, --force` | Skip confirmations |
| Filter | `-Filter` | `-F, --filter` | Filter tests by name |
| Report format | `-ReportFormat` | `-r, --report` | Coverage format |

#### Examples

```bash
# Run all tests
./ArcanisScripts/test/test.sh

# Unit tests with watch mode
./ArcanisScripts/test/test.sh unit --watch

# Generate coverage report
./ArcanisScripts/test/test.sh coverage --report html

# Run specific test
./ArcanisScripts/test/test.sh unit --filter "login"
```

#### Test Frameworks

| Framework | Language | Detection |
|-----------|----------|-----------|
| Jest | Node.js | `jest.config.js` |
| Mocha | Node.js | `.mocharc.yml` |
| Vitest | Node.js | `vitest.config.js` |
| cargo-test | Rust | `Cargo.toml` |
| go-test | Go | `go.mod` |
| NUnit/xUnit | .NET | `*.csproj` |
| Cypress | E2E | `cypress/` |
| Playwright | E2E | `playwright.config.*` |

---

## Deploy Scripts

### deploy.ps1 / deploy.sh

Deployment automation for staging, production, and rollback.

#### Usage

**PowerShell:**
```powershell
.\ArcanisScripts\deploy\deploy.ps1 [environment] [options]
```

**Bash:**
```bash
./ArcanisScripts/deploy/deploy.sh [environment] [options]
```

#### Environments

| Environment | Description |
|-------------|-------------|
| `staging` | Deploy to staging (default) |
| `production` | Deploy to production |
| `preview` | Deploy to preview |
| `rollback` | Rollback to previous version |
| `help` | Show help message |

#### Options

| Option | PowerShell | Bash | Description |
|--------|------------|------|-------------|
| Dry run | `-DryRun` | `-d, --dry-run` | Simulate deployment |
| Force | `-Force` | `-f, --force` | Skip confirmations |
| Skip tests | `-SkipTests` | `-s, --skip-tests` | Skip test execution |
| Verbose | `-Verbose` | `-v, --verbose` | Enable verbose output |
| Version | `-Version` | `-V, --version` | Specific version |

#### Examples

```bash
# Deploy to staging
./ArcanisScripts/deploy/deploy.sh staging

# Dry run to production
./ArcanisScripts/deploy/deploy.sh production --dry-run

# Deploy specific version
./ArcanisScripts/deploy/deploy.sh production --version "1.2.3"

# Rollback
./ArcanisScripts/deploy/deploy.sh rollback --force
```

#### Pre-deployment Checks

1. Git working directory must be clean
2. No unpushed commits (warning)
3. Tests pass (unless skipped)
4. Build succeeds

#### Deployment Providers

| Provider | Detection | Configuration |
|----------|-----------|---------------|
| Vercel | `vercel` in package.json | Automatic |
| AWS S3 | `aws-sdk` in package.json | Bucket name |
| Docker | `Dockerfile` exists | Registry URL |

---

## Setup Scripts

### setup.ps1 / setup.sh

Project initialization and dependency management.

#### Usage

**PowerShell:**
```powershell
.\ArcanisScripts\setup\setup.ps1 [action] [options]
```

**Bash:**
```bash
./ArcanisScripts/setup/setup.sh [action] [options]
```

#### Actions

| Action | Description | Default |
|--------|-------------|---------|
| `init` | Initialize new project | Yes |
| `install` | Install dependencies | No |
| `update` | Update dependencies | No |
| `reset` | Reset to clean state | No |
| `help` | Show help message | No |

#### Options

| Option | PowerShell | Bash | Description |
|--------|------------|------|-------------|
| Force | `-Force` | `-f, --force` | Skip confirmations |
| Verbose | `-Verbose` | `-v, --verbose` | Enable verbose output |
| Project type | `-ProjectType` | `-t, --type` | node/rust/go/dotnet/python |
| Project name | `-ProjectName` | `-n, --name` | Project name |

#### Examples

```bash
# Create Node.js project
./ArcanisScripts/setup/setup.sh init --type node --name "my-app"

# Create Rust project
./ArcanisScripts/setup/setup.sh init --type rust --name "my-crate"

# Install dependencies
./ArcanisScripts/setup/setup.sh install

# Update all dependencies
./ArcanisScripts/setup/setup.sh update

# Reset project
./ArcanisScripts/setup/setup.sh reset --force
```

#### Project Templates

| Type | Files Created |
|------|---------------|
| Node.js | package.json, tsconfig.json, src/, README.md, .gitignore |
| Rust | Cargo.toml, src/main.rs, README.md, .gitignore |
| Go | go.mod, main.go, README.md, .gitignore |
| .NET | *.csproj, Program.cs, README.md, .gitignore |
| Python | pyproject.toml, src/, tests/, README.md, .gitignore |

---

## Backup Scripts

### backup.ps1 / backup.sh

Backup creation, restoration, and management.

#### Usage

**PowerShell:**
```powershell
.\ArcanisScripts\backup\backup.ps1 [action] [options]
```

**Bash:**
```bash
./ArcanisScripts/backup/backup.sh [action] [options]
```

#### Actions

| Action | Description | Default |
|--------|-------------|---------|
| `create` | Create new backup | Yes |
| `restore` | Restore from backup | No |
| `list` | List available backups | No |
| `clean` | Remove old backups | No |
| `help` | Show help message | No |

#### Options

| Option | PowerShell | Bash | Description |
|--------|------------|------|-------------|
| Force | `-Force` | `-f, --force` | Skip confirmations |
| Verbose | `-Verbose` | `-v, --verbose` | Enable verbose output |
| Source | `-Source` | `-s, --source` | Source directory |
| Destination | `-Destination` | `-d, --destination` | Backup location |
| Retention | `-Retention` | `-r, --retention` | Retention period |

#### Examples

```bash
# Create backup
./ArcanisScripts/backup/backup.sh

# Backup specific directory
./ArcanisScripts/backup/backup.sh create --source /path/to/project

# List backups
./ArcanisScripts/backup/backup.sh list

# Restore latest backup
./ArcanisScripts/backup/backup.sh restore

# Clean old backups
./ArcanisScripts/backup/backup.sh clean --retention "7d"
```

#### Backup Contents

Each backup includes:
- All project files
- Metadata (JSON)
- Compressed archive

Excluded directories:
- `node_modules/`
- `.git/`
- `dist/`
- `build/`
- `target/`
- `__pycache__/`
- `.venv/`

---

## Config Scripts

### config.ps1 / config.sh

Environment variable management.

#### Usage

**PowerShell:**
```powershell
.\ArcanisScripts\config\config.ps1 [action] [options]
```

**Bash:**
```bash
./ArcanisScripts/config/config.sh [action] [options]
```

#### Actions

| Action | Description | Default |
|--------|-------------|---------|
| `init` | Initialize .env file | No |
| `set` | Set variable | No |
| `get` | Get variable | No |
| `list` | List all variables | Yes |
| `validate` | Validate required vars | No |
| `export` | Export to file | No |
| `import` | Import from file | No |
| `help` | Show help message | No |

#### Options

| Option | PowerShell | Bash | Description |
|--------|------------|------|-------------|
| Force | `-Force` | `-f, --force` | Skip confirmations |
| Verbose | `-Verbose` | `-v, --verbose` | Enable verbose output |
| Name | `-Name` | `-n, --name` | Variable name |
| Value | `-Value` | `-V, --value` | Variable value |
| Environment | `-Environment` | `-e, --environment` | Target environment |
| File | `-File` | `-F, --file` | Environment file |

#### Examples

```bash
# Initialize environment
./ArcanisScripts/config/config.sh init

# Set variable
./ArcanisScripts/config/config.sh set --name "API_KEY" --value "abc123"

# Get variable
./ArcanisScripts/config/config.sh get --name "DATABASE_URL"

# List all
./ArcanisScripts/config/config.sh list

# Validate
./ArcanisScripts/config/config.sh validate

# Export
./ArcanisScripts/config/config.sh export --file ".env.production"
```

#### Sensitive Variables

Variables containing these strings are masked in output:
- SECRET
- PASSWORD
- KEY
- TOKEN

---

## Library Functions

### common.ps1 / common.sh

Shared utility functions for all scripts.

#### Functions

| Function | Description |
|----------|-------------|
| `Write-Log` / `log_*` | Colored logging output |
| `Test-CommandExists` / `command_exists` | Check if command exists |
| `Get-ProjectRoot` / `get_project_root` | Find project root directory |
| `Invoke-SafeCommand` / `invoke_safe_command` | Execute command with error handling |
| `Confirm-Action` / `confirm_action` | User confirmation prompt |
| `Test-Dependencies` / `test_dependencies` | Check required tools |

#### Log Levels

| Level | Color | Usage |
|-------|-------|-------|
| Info | Cyan | General information |
| Warning | Yellow | Non-critical issues |
| Error | Red | Critical failures |
| Success | Green | Operation completed |

#### Usage in Custom Scripts

**PowerShell:**
```powershell
. "$PSScriptRoot\..\lib\common.ps1"

Write-Log "Starting operation..." -Level Info
Invoke-SafeCommand "npm test" "Run tests"
```

**Bash:**
```bash
source "$SCRIPT_DIR/../lib/common.sh"

log_info "Starting operation..."
invoke_safe_command "npm test" "Run tests"
```
