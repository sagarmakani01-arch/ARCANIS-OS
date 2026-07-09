# ArcanisScripts

A comprehensive, cross-platform script library for automating development workflows.

## Overview

ArcanisScripts provides a set of well-documented, safe, and reusable scripts for:

- **Build Automation** - Compile, bundle, and package your projects
- **Testing Automation** - Run unit, integration, and E2E tests
- **Deployment** - Deploy to staging, production, or preview environments
- **Setup Scripts** - Initialize new projects and manage dependencies
- **Backup Tools** - Create and restore project backups
- **Environment Configuration** - Manage environment variables securely

## Features

- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Project Agnostic**: Supports Node.js, Rust, Go, .NET, and Python projects
- **Safe Execution**: Includes confirmation prompts and error handling
- **Well Documented**: Comprehensive help for all commands
- **Modular Design**: Use only what you need

## Quick Start

### Windows (PowerShell)

```powershell
# Get help for any script
.\ArcanisScripts\build\build.ps1 help
.\ArcanisScripts\test\test.ps1 help
.\ArcanisScripts\deploy\deploy.ps1 help

# Initialize a new project
.\ArcanisScripts\setup\setup.ps1 init -ProjectType node -ProjectName "my-app"

# Build your project
.\ArcanisScripts\build\build.ps1

# Run tests
.\ArcanisScripts\test\test.ps1

# Deploy to staging
.\ArcanisScripts\deploy\deploy.ps1 staging
```

### Linux/macOS (Bash)

```bash
# Make scripts executable (first time only)
chmod +x ArcanisScripts/**/*.sh

# Get help for any script
./ArcanisScripts/build/build.sh help
./ArcanisScripts/test/test.sh help
./ArcanisScripts/deploy/deploy.sh help

# Initialize a new project
./ArcanisScripts/setup/setup.sh init --type node --name "my-app"

# Build your project
./ArcanisScripts/build/build.sh

# Run tests
./ArcanisScripts/test/test.sh

# Deploy to staging
./ArcanisScripts/deploy/deploy.sh staging
```

## Directory Structure

```
ArcanisScripts/
├── build/              # Build automation scripts
│   ├── build.ps1       # PowerShell build script
│   └── build.sh        # Bash build script
├── test/               # Testing automation scripts
│   ├── test.ps1        # PowerShell test script
│   └── test.sh         # Bash test script
├── deploy/             # Deployment scripts
│   ├── deploy.ps1      # PowerShell deploy script
│   └── deploy.sh       # Bash deploy script
├── setup/              # Project setup scripts
│   ├── setup.ps1       # PowerShell setup script
│   └── setup.sh        # Bash setup script
├── backup/             # Backup and restore tools
│   ├── backup.ps1      # PowerShell backup script
│   └── backup.sh       # Bash backup script
├── config/             # Environment configuration
│   ├── config.ps1      # PowerShell config script
│   └── config.sh       # Bash config script
├── lib/                # Shared libraries
│   ├── common.ps1      # PowerShell utilities
│   └── common.sh       # Bash utilities
├── docs/               # Documentation
│   ├── USAGE.md        # Detailed usage guide
│   └── SCRIPTS.md      # Script reference
└── README.md           # This file
```

## Scripts Reference

### Build Scripts

| Command | Description |
|---------|-------------|
| `build all` | Build all targets (default) |
| `build clean` | Clean build artifacts |
| `build compile` | Compile source code |
| `build bundle` | Bundle for distribution |
| `build docker` | Build Docker image |

### Test Scripts

| Command | Description |
|---------|-------------|
| `test all` | Run all tests (default) |
| `test unit` | Run unit tests only |
| `test integration` | Run integration tests only |
| `test e2e` | Run end-to-end tests |
| `test coverage` | Generate coverage report |
| `test lint` | Run linter |

### Deploy Scripts

| Command | Description |
|---------|-------------|
| `deploy staging` | Deploy to staging (default) |
| `deploy production` | Deploy to production |
| `deploy preview` | Deploy to preview |
| `deploy rollback` | Rollback to previous version |

### Setup Scripts

| Command | Description |
|---------|-------------|
| `setup init` | Initialize a new project |
| `setup install` | Install dependencies |
| `setup update` | Update dependencies |
| `setup reset` | Reset project to clean state |

### Backup Scripts

| Command | Description |
|---------|-------------|
| `backup create` | Create a new backup (default) |
| `backup restore` | Restore from a backup |
| `backup list` | List available backups |
| `backup clean` | Remove old backups |

### Config Scripts

| Command | Description |
|---------|-------------|
| `config init` | Initialize .env file |
| `config set` | Set an environment variable |
| `config get` | Get an environment variable |
| `config list` | List all variables (default) |
| `config validate` | Validate required variables |
| `config export` | Export variables to file |
| `config import` | Import variables from file |

## Supported Project Types

- **Node.js** - npm, yarn, pnpm with TypeScript support
- **Rust** - Cargo with Clippy integration
- **Go** - Modules with golangci-lint support
- **.NET** - dotnet CLI with MSBuild
- **Python** - pip, poetry, with venv support

## Configuration

### Customizing Scripts

Each script can be customized via command-line options. Run any script with `help` to see available options.

### Global Configuration

Create an `.arcanisrc` file in your project root:

```json
{
  "build": {
    "output": "./dist",
    "configuration": "Release"
  },
  "deploy": {
    "provider": "vercel",
    "staging": {
      "url": "https://staging.example.com"
    },
    "production": {
      "url": "https://example.com"
    }
  },
  "backup": {
    "retention": "30d",
    "destination": "./backups"
  }
}
```

## Safety Features

- **Confirmation Prompts**: All destructive operations require confirmation
- **Dry Run Mode**: Test commands without making changes
- **Backup Before Deploy**: Automatic backups before deployments
- **Rollback Support**: Easy rollback to previous versions
- **Error Handling**: Comprehensive error checking and reporting

## Examples

### Complete Development Workflow

```bash
# 1. Initialize a new project
./ArcanisScripts/setup/setup.sh init --type node --name "my-api"

# 2. Configure environment
./ArcanisScripts/config/config.sh init
./ArcanisScripts/config/config.sh set --name "DATABASE_URL" --value "postgres://..."

# 3. Install dependencies
./ArcanisScripts/setup/setup.sh install

# 4. Build the project
./ArcanisScripts/build/build.sh

# 5. Run tests
./ArcanisScripts/test/test.sh

# 6. Create a backup
./ArcanisScripts/backup/backup.sh create

# 7. Deploy to staging
./ArcanisScripts/deploy/deploy.sh staging

# 8. Deploy to production
./ArcanisScripts/deploy/deploy.sh production
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build
        run: ./ArcanisScripts/build/build.sh
      
      - name: Test
        run: ./ArcanisScripts/test/test.sh
      
      - name: Deploy to Staging
        if: github.ref == 'refs/heads/main'
        run: ./ArcanisScripts/deploy/deploy.sh staging --force
```

## Troubleshooting

### Common Issues

1. **Permission Denied (Linux/macOS)**
   ```bash
   chmod +x ArcanisScripts/**/*.sh
   ```

2. **Command Not Found**
   - Ensure scripts are in your PATH
   - Or run with full path

3. **Missing Dependencies**
   - Run `setup install` to install required tools
   - Check individual script help for specific requirements

### Getting Help

Each script includes comprehensive help:

```bash
# PowerShell
.\ArcanisScripts\<script>\<script>.ps1 help

# Bash
./ArcanisScripts/<script>/<script>.sh help
```

## Contributing

1. Follow the existing code style
2. Add help text for new commands
3. Include error handling
4. Update documentation
5. Test on multiple platforms

## License

MIT License - See LICENSE file for details.

## Support

- Documentation: See `docs/` directory
- Issues: Report bugs via GitHub Issues
- Community: Join our Discord server
