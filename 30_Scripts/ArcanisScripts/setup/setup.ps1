# ArcanisScripts Setup Automation
# Usage: .\setup.ps1 [action] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("init", "install", "update", "reset", "help")]
    [string]$Action = "init",
    
    [switch]$Force,
    [switch]$Verbose,
    [string]$ProjectType = "node",
    [string]$ProjectName = "my-project"
)

. "$PSScriptRoot\..\lib\common.ps1"

function Show-Help {
    Write-Host @"
ArcanisScripts Setup Automation

Usage: .\setup.ps1 [action] [options]

Actions:
    init         Initialize a new project (default)
    install      Install dependencies
    update       Update dependencies
    reset        Reset project to clean state
    help         Show this help message

Options:
    -Force           Skip confirmation prompts
    -Verbose         Enable verbose output
    -ProjectType     Project type (node, rust, go, dotnet, python)
    -ProjectName     Name for new project

Examples:
    .\setup.ps1 init -ProjectType node -ProjectName "my-app"
    .\setup.ps1 install
    .\setup.ps1 update
    .\setup.ps1 reset -Force
"@
}

function Initialize-Project {
    Write-Log "Initializing new project: $ProjectName" -Level Info
    
    if (Test-Path $ProjectName) {
        if (-not $Force) {
            $continue = Confirm-Action "Directory '$ProjectName' exists. Overwrite?"
            if (-not $continue) { return }
        }
        Remove-Item -Recurse -Force $ProjectName
    }
    
    New-Item -ItemType Directory -Path $ProjectName -Force | Out-Null
    
    switch ($ProjectType) {
        "node" {
            Write-Log "Creating Node.js project..." -Level Info
            Push-Location $ProjectName
            Invoke-SafeCommand "npm init -y" "Initialize npm"
            Invoke-SafeCommand "npm install typescript @types/node --save-dev" "Install TypeScript"
            Invoke-SafeCommand "npx tsc --init" "Initialize TypeScript"
            Pop-Location
        }
        "rust" {
            Write-Log "Creating Rust project..." -Level Info
            Push-Location (Split-Path -Parent $PWD)
            Invoke-SafeCommand "cargo new $ProjectName" "Initialize Cargo project"
            Pop-Location
        }
        "go" {
            Write-Log "Creating Go project..." -Level Info
            Push-Location $ProjectName
            $modulePath = "github.com/username/$ProjectName"
            Invoke-SafeCommand "go mod init $modulePath" "Initialize Go module"
            Pop-Location
        }
        "dotnet" {
            Write-Log "Creating .NET project..." -Level Info
            Push-Location (Split-Path -Parent $PWD)
            Invoke-SafeCommand "dotnet new console -n $ProjectName" "Initialize .NET project"
            Pop-Location
        }
        "python" {
            Write-Log "Creating Python project..." -Level Info
            Push-Location $ProjectName
            @"
[project]
name = "$ProjectName"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.8"
"@ | Out-File -FilePath "pyproject.toml" -Encoding UTF8
            
            New-Item -ItemType Directory -Path "src" -Force | Out-Null
            New-Item -ItemType Directory -Path "tests" -Force | Out-Null
            Pop-Location
        }
    }
    
    # Create common files
    Push-Location $ProjectName
    
    @"
# $ProjectName

## Description
Brief description of your project.

## Installation
```bash
# Add installation instructions here
```

## Usage
```bash
# Add usage examples here
```

## License
MIT
"@ | Out-File -FilePath "README.md" -Encoding UTF8

    @"
node_modules/
dist/
build/
.env
.env.local
*.log
.DS_Store
Thumbs.db
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

    Pop-Location
    
    Write-Log "Project '$ProjectName' created successfully!" -Level Success
}

function Install-Dependencies {
    Write-Log "Installing dependencies..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        Invoke-SafeCommand "npm install" "Install npm dependencies"
    }
    elseif (Test-Path "$root\Cargo.toml") {
        Invoke-SafeCommand "cargo fetch" "Fetch Rust dependencies"
    }
    elseif (Test-Path "$root\go.mod") {
        Invoke-SafeCommand "go mod download" "Download Go modules"
    }
    elseif (Test-Path "$root\*.csproj" -PathType Leaf) {
        Invoke-SafeCommand "dotnet restore" "Restore .NET packages"
    }
    elseif (Test-Path "$root\requirements.txt") {
        Invoke-SafeCommand "pip install -r requirements.txt" "Install Python packages"
    }
    elseif (Test-Path "$root\pyproject.toml") {
        Invoke-SafeCommand "pip install -e ." "Install Python package"
    }
    else {
        Write-Log "No dependency file found" -Level Warning
    }
}

function Update-Dependencies {
    Write-Log "Updating dependencies..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        Invoke-SafeCommand "npm update" "Update npm packages"
        Invoke-SafeCommand "npm audit fix" "Fix security vulnerabilities"
    }
    elseif (Test-Path "$root\Cargo.toml") {
        Invoke-SafeCommand "cargo update" "Update Cargo packages"
    }
    elseif (Test-Path "$root\go.mod") {
        Invoke-SafeCommand "go get -u ./..." "Update Go modules"
        Invoke-SafeCommand "go mod tidy" "Tidy Go modules"
    }
    elseif (Test-Path "$root\*.csproj" -PathType Leaf) {
        Invoke-SafeCommand "dotnet list package --outdated" "Check for updates"
    }
    elseif (Test-Path "$root\requirements.txt") {
        Write-Log "For Python, consider using: pip install --upgrade -r requirements.txt" -Level Info
    }
}

function Reset-Project {
    Write-Log "Resetting project..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (-not $Force) {
        $continue = Confirm-Action "This will remove all untracked files and reset changes. Continue?"
        if (-not $continue) { return }
    }
    
    # Clean build artifacts
    & "$PSScriptRoot\..\build\build.ps1" clean
    
    # Reset git if in a repo
    if (Test-Path "$root\.git") {
        Push-Location $root
        Invoke-SafeCommand "git clean -fd" "Remove untracked files"
        Invoke-SafeCommand "git checkout -- ." "Reset changes"
        Pop-Location
    }
    
    # Reinstall dependencies
    Install-Dependencies
    
    Write-Log "Project reset completed" -Level Success
}

# Main execution
switch ($Action) {
    "init" { Initialize-Project }
    "install" { Install-Dependencies }
    "update" { Update-Dependencies }
    "reset" { Reset-Project }
    "help" { Show-Help }
}
