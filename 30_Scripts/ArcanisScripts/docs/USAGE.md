# ArcanisScripts Usage Guide

This guide provides detailed instructions for using ArcanisScripts in your development workflow.

## Table of Contents

1. [Installation](#installation)
2. [Build Automation](#build-automation)
3. [Testing Automation](#testing-automation)
4. [Deployment](#deployment)
5. [Project Setup](#project-setup)
6. [Backup and Restore](#backup-and-restore)
7. [Environment Configuration](#environment-configuration)
8. [Advanced Usage](#advanced-usage)

## Installation

### Windows (PowerShell)

1. Copy the `ArcanisScripts` folder to your project or a shared location
2. Open PowerShell and navigate to your project
3. Run scripts using the full path or add to your PowerShell profile

```powershell
# Add to PowerShell profile for global access
$env:PATH += ";C:\path\to\ArcanisScripts"

# Or create a symlink
New-Item -ItemType SymbolicLink -Path "C:\Users\YourUser\Documents\WindowsPowerShell\Modules\ArcanisScripts" -Target "C:\path\to\ArcanisScripts"
```

### Linux/macOS (Bash)

1. Clone or copy the `ArcanisScripts` folder
2. Make scripts executable:

```bash
chmod +x ArcanisScripts/**/*.sh

# Optional: Add to PATH
echo 'export PATH="$PATH:/path/to/ArcanisScripts"' >> ~/.bashrc
source ~/.bashrc
```

## Build Automation

### Basic Usage

```powershell
# Windows
.\ArcanisScripts\build\build.ps1

# Linux/macOS
./ArcanisScripts/build/build.sh
```

### Available Targets

#### All (Default)
Builds the entire project:

```bash
# Detects project type and runs appropriate build
./ArcanisScripts/build/build.sh all
```

#### Clean
Removes build artifacts:

```bash
./ArcanisScripts/build/build.sh clean
```

Removes:
- `dist/`
- `build/`
- `target/`
- `node_modules/.cache`
- `.next`

#### Compile
Compiles source code based on project type:

```bash
./ArcanisScripts/build/build.sh compile
```

**Node.js/TypeScript:**
- Runs `npm run build`
- Supports both JavaScript and TypeScript projects

**Rust:**
- Runs `cargo build --release`
- Use `-C Debug` for debug builds

**Go:**
- Runs `go build -o dist/app`
- Outputs to configured directory

**.NET:**
- Runs `dotnet build -c Release`
- Supports all .NET project types

#### Bundle
Creates a distributable archive:

```bash
./ArcanisScripts/build/build.sh bundle
```

Creates:
- Timestamped archive (ZIP on Windows, tar.gz on Linux/macOS)
- Includes build artifacts and configuration files
- Output in `./dist/` directory

#### Docker
Builds a Docker image:

```bash
./ArcanisScripts/build/build.sh docker
```

Requirements:
- `Dockerfile` in project root
- Docker installed and running

### Build Options

```bash
# PowerShell
.\ArcanisScripts\build\build.ps1 -Target compile -Configuration Debug -Verbose

# Bash
./ArcanisScripts/build/build.sh compile --config Debug --verbose
```

| Option | Description |
|--------|-------------|
| `-Clean` / `-c` | Clean before building |
| `-Verbose` / `-v` | Enable verbose output |
| `-Force` / `-f` | Skip confirmation prompts |
| `-Configuration` / `-C` | Build configuration (Debug/Release) |
| `-OutputDir` / `-o` | Output directory |

## Testing Automation

### Running Tests

```bash
# Run all tests (unit + integration + lint)
./ArcanisScripts/test/test.sh

# Run specific test type
./ArcanisScripts/test/test.sh unit
./ArcanisScripts/test/test.sh integration
./ArcanisScripts/test/test.sh e2e
```

### Test Types

#### Unit Tests
Fast, isolated tests:

```bash
./ArcanisScripts/test/test.sh unit
```

#### Integration Tests
Tests that interact with external services:

```bash
./ArcanisScripts/test/test.sh integration
```

#### End-to-End Tests
Full application tests:

```bash
./ArcanisScripts/test/test.sh e2e
```

Supports:
- Cypress
- Playwright
- Custom E2E frameworks

### Coverage Reports

Generate test coverage:

```bash
./ArcanisScripts/test/test.sh coverage
```

**Node.js:** Uses nyc or istanbul
**Rust:** Uses cargo-tarpaulin (install: `cargo install cargo-tarpaulin`)
**Go:** Built-in coverage tools

### Linting

Run code quality checks:

```bash
./ArcanisScripts/test/test.sh lint
```

**Node.js:** ESLint
**Rust:** Clippy
**Go:** golangci-lint or go vet
**.NET:** dotnet-format

### Test Options

```bash
# Watch mode for development
./ArcanisScripts/test/test.sh unit --watch

# Filter tests by name
./ArcanisScripts/test/test.sh unit --filter "login"

# Generate HTML coverage report
./ArcanisScripts/test/test.sh coverage --report html
```

## Deployment

### Environments

```bash
# Deploy to staging (default)
./ArcanisScripts/deploy/deploy.sh staging

# Deploy to production
./ArcanisScripts/deploy/deploy.sh production

# Deploy to preview
./ArcanisScripts/deploy/deploy.sh preview
```

### Deployment Process

1. **Pre-deployment Checks**
   - Verifies clean git working directory
   - Checks for unpushed commits
   - Runs tests (unless skipped)

2. **Build**
   - Compiles source code
   - Creates deployment artifacts

3. **Deploy**
   - Pushes to configured provider
   - Tags release if version specified

### Supported Providers

- **Vercel** - Automatic detection from package.json
- **AWS S3** - For static sites
- **Docker** - Container-based deployments
- **Custom** - Extend via deployment configuration

### Rollback

Quick rollback to previous version:

```bash
./ArcanisScripts/deploy/deploy.sh rollback
```

### Deployment Options

```bash
# Dry run (simulate without executing)
./ArcanisScripts/deploy/deploy.sh production --dry-run

# Deploy specific version
./ArcanisScripts/deploy/deploy.sh production --version "1.2.3"

# Skip tests
./ArcanisScripts/deploy/deploy.sh production --skip-tests

# Force deployment
./ArcanisScripts/deploy/deploy.sh production --force
```

### Deployment Configuration

Create `.deploy.json` in your project root:

```json
{
  "staging": {
    "url": "https://staging.example.com",
    "provider": "vercel"
  },
  "production": {
    "url": "https://example.com",
    "provider": "vercel",
    "branch": "main"
  }
}
```

## Project Setup

### Initialize New Project

```bash
# Node.js project
./ArcanisScripts/setup/setup.sh init --type node --name "my-app"

# Rust project
./ArcanisScripts/setup/setup.sh init --type rust --name "my-crate"

# Go project
./ArcanisScripts/setup/setup.sh init --type go --name "my-module"

# .NET project
./ArcanisScripts/setup/setup.sh init --type dotnet --name "my-app"

# Python project
./ArcanisScripts/setup/setup.sh init --type python --name "my-package"
```

### Created Structure

Each project type creates:

- **README.md** - Project documentation template
- **.gitignore** - Standard ignore patterns
- **Project files** - Type-specific configuration
- **Source directories** - Standard project structure

### Manage Dependencies

```bash
# Install all dependencies
./ArcanisScripts/setup/setup.sh install

# Update dependencies
./ArcanisScripts/setup/setup.sh update

# Reset project (clean + reinstall)
./ArcanisScripts/setup/setup.sh reset
```

## Backup and Restore

### Create Backup

```bash
# Backup current directory
./ArcanisScripts/backup/backup.sh

# Backup specific directory
./ArcanisScripts/backup/backup.sh create --source /path/to/project

# Backup to custom location
./ArcanisScripts/backup/backup.sh create --destination /backups
```

### Backup Contents

Each backup includes:
- All project files (excluding node_modules, .git, etc.)
- Metadata (timestamp, hostname, file count, size)
- Compressed archive (ZIP or tar.gz)

### List Backups

```bash
./ArcanisScripts/backup/backup.sh list
```

Output:
```
Date                    Size        Name
------------------------------------------------------------
2024-01-15 14:30:00    2.45 MB     backup_20240115_143000.tar.gz
2024-01-14 10:00:00    2.32 MB     backup_20240114_100000.tar.gz
```

### Restore Backup

```bash
# Restore latest backup
./ArcanisScripts/backup/backup.sh restore

# Force restore (skip confirmation)
./ArcanisScripts/backup/backup.sh restore --force
```

### Clean Old Backups

```bash
# Remove backups older than 30 days (default)
./ArcanisScripts/backup/backup.sh clean

# Custom retention period
./ArcanisScripts/backup/backup.sh clean --retention "7d"
```

## Environment Configuration

### Initialize Environment

```bash
./ArcanisScripts/config/config.sh init
```

Creates:
- `.env` - Environment variables with sample values
- `.env.example` - Template without sensitive data
- Updates `.gitignore` to exclude .env files

### Manage Variables

```bash
# List all variables
./ArcanisScripts/config/config.sh list

# Set a variable
./ArcanisScripts/config/config.sh set --name "API_KEY" --value "abc123"

# Get a variable
./ArcanisScripts/config/config.sh get --name "DATABASE_URL"

# Validate required variables
./ArcanisScripts/config/config.sh validate
```

### Export/Import

```bash
# Export current environment
./ArcanisScripts/config/config.sh export --file ".env.production"

# Import from file
./ArcanisScripts/config/config.sh import --file ".env.staging"
```

### Sensitive Data Protection

The config script automatically masks sensitive values:

- Variables containing: SECRET, PASSWORD, KEY, TOKEN
- Displayed as `***` in list output
- Never logged in verbose mode

## Advanced Usage

### Combining Scripts

Create workflow scripts that combine multiple operations:

**deploy-all.sh:**
```bash
#!/bin/bash
source ArcanisScripts/lib/common.sh

log_info "Starting full deployment workflow"

# Clean
./ArcanisScripts/build/build.sh clean

# Test
./ArcanisScripts/test/test.sh unit

# Build
./ArcanisScripts/build/build.sh compile

# Backup
./ArcanisScripts/backup/backup.sh create

# Deploy
./ArcanisScripts/deploy/deploy.sh staging

log_success "Deployment complete!"
```

### Custom Configuration

Extend scripts by creating `.arcanisrc`:

```json
{
  "build": {
    "output": "./dist",
    "configuration": "Release",
    "exclude": ["test", "docs"]
  },
  "test": {
    "coverage": true,
    "threshold": 80
  },
  "deploy": {
    "preDeploy": ["test", "lint"],
    "postDeploy": ["notify"]
  }
}
```

### Environment-Specific Configs

Create environment-specific configurations:

```bash
# Development
./ArcanisScripts/config/config.sh init --environment development

# Staging
./ArcanisScripts/config/config.sh import --file ".env.staging"

# Production
./ArcanisScripts/config/config.sh import --file ".env.production"
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: CI/CD
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup
        run: ./ArcanisScripts/setup/setup.sh install
      
      - name: Lint
        run: ./ArcanisScripts/test/test.sh lint
      
      - name: Test
        run: ./ArcanisScripts/test/test.sh unit
      
      - name: Build
        run: ./ArcanisScripts/build/build.sh
      
      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: ./ArcanisScripts/deploy/deploy.sh production --force
```

#### GitLab CI

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - ./ArcanisScripts/test/test.sh lint
    - ./ArcanisScripts/test/test.sh unit

build:
  stage: build
  script:
    - ./ArcanisScripts/build/build.sh
  artifacts:
    paths:
      - dist/

deploy:
  stage: deploy
  script:
    - ./ArcanisScripts/deploy/deploy.sh production
  only:
    - main
```

## Troubleshooting

### Common Issues

#### "Command not found" Error

**Windows:**
```powershell
# Run with full path
C:\path\to\ArcanisScripts\build\build.ps1

# Or add to PATH
$env:PATH += ";C:\path\to\ArcanisScripts"
```

**Linux/macOS:**
```bash
# Make executable
chmod +x ArcanisScripts/**/*.sh

# Or run with bash
bash ArcanisScripts/build/build.sh
```

#### "Permission denied" Error

```bash
# Fix permissions
chmod +x ArcanisScripts/**/*.sh

# Or run as administrator (Windows)
Start-Process powershell -Verb RunAs
```

#### Missing Dependencies

```bash
# Install required tools
./ArcanisScripts/setup/setup.sh install

# Check what's installed
which node npm cargo go dotnet
```

#### Build Fails

1. Check project type is detected correctly
2. Ensure dependencies are installed
3. Run with verbose flag for details
4. Check build output for specific errors

#### Tests Fail

1. Run tests individually to isolate issue
2. Check test configuration
3. Verify test dependencies
4. Review test output for details

### Getting Help

Each script includes comprehensive help:

```bash
# PowerShell
.\ArcanisScripts\<script>\<script>.ps1 help

# Bash
./ArcanisScripts/<script>/<script>.sh help
```

### Debug Mode

Enable verbose output for debugging:

```bash
# PowerShell
.\ArcanisScripts\build\build.ps1 -Verbose

# Bash
./ArcanisScripts/build/build.sh --verbose
```

## Best Practices

1. **Version Control**: Keep ArcanisScripts in your repository or as a submodule
2. **Environment Variables**: Never commit `.env` files
3. **Backups**: Create backups before major changes
4. **Testing**: Always run tests before deployment
5. **Documentation**: Keep scripts documentation updated
6. **Modularity**: Use only the scripts you need
7. **Safety**: Use dry-run mode for testing commands

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to ArcanisScripts.
