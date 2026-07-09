# ArcanisScripts Environment Configuration
# Usage: .\config.ps1 [action] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("init", "set", "get", "list", "validate", "export", "import", "help")]
    [string]$Action = "list",
    
    [switch]$Force,
    [switch]$Verbose,
    [string]$Name = "",
    [string]$Value = "",
    [string]$Environment = "development",
    [string]$File = ".env"
)

. "$PSScriptRoot\..\lib\common.ps1"

function Show-Help {
    Write-Host @"
ArcanisScripts Environment Configuration

Usage: .\config.ps1 [action] [options]

Actions:
    init         Initialize .env file from template
    set          Set an environment variable
    get          Get an environment variable value
    list         List all environment variables (default)
    validate     Validate required environment variables
    export       Export environment variables to file
    import       Import environment variables from file
    help         Show this help message

Options:
    -Force           Skip confirmation prompts
    -Verbose         Enable verbose output
    -Name            Variable name
    -Value           Variable value
    -Environment     Target environment (development, staging, production)
    -File            Environment file path (default: .env)

Examples:
    .\config.ps1 init
    .\config.ps1 set -Name "API_KEY" -Value "abc123"
    .\config.ps1 get -Name "DATABASE_URL"
    .\config.ps1 list
    .\config.ps1 validate
    .\config.ps1 export -File ".env.production"
    .\config.ps1 import -File ".env.example"
"@
}

function Initialize-Environment {
    Write-Log "Initializing environment configuration..." -Level Info
    
    $root = Get-ProjectRoot
    $envFile = Join-Path $root $File
    
    if ((Test-Path $envFile) -and (-not $Force)) {
        $continue = Confirm-Action "$File already exists. Overwrite?"
        if (-not $continue) { return }
    }
    
    # Create .env file with common variables
    $template = @"
# ArcanisScripts Environment Configuration
# Environment: $Environment
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Application
APP_NAME=my-app
APP_VERSION=1.0.0
APP_ENV=$Environment
APP_DEBUG=false
APP_PORT=3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DATABASE_POOL_SIZE=10

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
API_KEY=
API_SECRET=

# Authentication
JWT_SECRET=
JWT_EXPIRATION=24h

# Logging
LOG_LEVEL=info
LOG_FILE=logs/app.log

# Services
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
"@

    $template | Out-File -FilePath $envFile -Encoding UTF8
    
    # Create .env.example (without sensitive values)
    $exampleTemplate = $template -replace '=password', '=\*\*\*'
    $exampleTemplate = $exampleTemplate -replace 'API_KEY=.*', 'API_KEY=your-api-key'
    $exampleTemplate = $exampleTemplate -replace 'API_SECRET=.*', 'API_SECRET=your-api-secret'
    $exampleTemplate = $exampleTemplate -replace 'JWT_SECRET=.*', 'JWT_SECRET=your-jwt-secret'
    
    $exampleTemplate | Out-File -FilePath "$root\.env.example" -Encoding UTF8
    
    # Create .gitignore entry if not exists
    $gitignore = Join-Path $root ".gitignore"
    if (Test-Path $gitignore) {
        $content = Get-Content $gitignore -Raw
        if ($content -notmatch '\.env$') {
            "`n.env`n.env.local`n.env.*.local" | Out-File -FilePath $gitignore -Append -Encoding UTF8
        }
    }
    
    Write-Log "Environment files created:" -Level Success
    Write-Log "  - $File (with values)" -Level Info
    Write-Log "  - .env.example (template)" -Level Info
}

function Set-EnvironmentVariable {
    param([string]$VarName, [string]$VarValue)
    
    if ([string]::IsNullOrEmpty($VarName)) {
        Write-Log "Variable name is required" -Level Error
        return
    }
    
    $root = Get-ProjectRoot
    $envFile = Join-Path $root $File
    
    if (-not (Test-Path $envFile)) {
        Write-Log "Environment file not found. Run 'init' first." -Level Error
        return
    }
    
    $content = Get-Content $envFile -Raw
    
    # Check if variable exists
    if ($content -match "^$VarName=.*$" -Multiline) {
        # Update existing variable
        $content = $content -replace "^$VarName=.*$", "$VarName=$VarValue"
    } else {
        # Add new variable
        $content = "$content`n$VarName=$VarValue"
    }
    
    $content | Out-File -FilePath $envFile -Encoding UTF8
    
    Write-Log "Set $VarName=$VarValue" -Level Success
}

function Get-EnvironmentVariable {
    param([string]$VarName)
    
    if ([string]::IsNullOrEmpty($VarName)) {
        Write-Log "Variable name is required" -Level Error
        return
    }
    
    $root = Get-ProjectRoot
    $envFile = Join-Path $root $File
    
    if (-not (Test-Path $envFile)) {
        Write-Log "Environment file not found" -Level Error
        return
    }
    
    $content = Get-Content $envFile
    
    foreach ($line in $content) {
        if ($line -match "^$VarName=(.*)$") {
            Write-Output $matches[1]
            return
        }
    }
    
    Write-Log "Variable '$VarName' not found" -Level Warning
}

function Get-EnvironmentList {
    Write-Log "Environment variables ($File):" -Level Info
    
    $root = Get-ProjectRoot
    $envFile = Join-Path $root $File
    
    if (-not (Test-Path $envFile)) {
        Write-Log "Environment file not found" -Level Error
        return
    }
    
    $content = Get-Content $envFile
    
    Write-Host "`nVariable                      Value"
    Write-Host "-" * 60
    
    foreach ($line in $content) {
        if ($line -match "^([^#=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2]
            
            # Mask sensitive values
            if ($name -match "(SECRET|PASSWORD|KEY|TOKEN)") {
                $value = "***"
            }
            
            # Truncate long values
            if ($value.Length -gt 30) {
                $value = $value.Substring(0, 27) + "..."
            }
            
            Write-Host ("{0,-30} {1}" -f $name, $value)
        }
    }
}

function Test-EnvironmentVariables {
    Write-Log "Validating environment variables..." -Level Info
    
    $root = Get-ProjectRoot
    $envFile = Join-Path $root $File
    
    if (-not (Test-Path $envFile)) {
        Write-Log "Environment file not found" -Level Error
        return
    }
    
    $requiredVars = @(
        "APP_NAME",
        "APP_ENV",
        "DATABASE_URL",
        "API_KEY"
    )
    
    $content = Get-Content $envFile -Raw
    $missing = @()
    
    foreach ($var in $requiredVars) {
        if ($content -notmatch "^$var=.+$" -Multiline) {
            $missing += $var
        }
    }
    
    if ($missing.Count -eq 0) {
        Write-Log "All required variables are set" -Level Success
    } else {
        Write-Log "Missing required variables:" -Level Error
        foreach ($var in $missing) {
            Write-Log "  - $var" -Level Error
        }
    }
}

function Export-EnvironmentVariables {
    param([string]$OutputFile)
    
    Write-Log "Exporting environment variables..." -Level Info
    
    $root = Get-ProjectRoot
    $sourceFile = Join-Path $root $File
    $destFile = Join-Path $root $OutputFile
    
    if (-not (Test-Path $sourceFile)) {
        Write-Log "Source environment file not found" -Level Error
        return
    }
    
    Copy-Item -Path $sourceFile -Destination $destFile -Force
    
    Write-Log "Exported to: $OutputFile" -Level Success
}

function Import-EnvironmentVariables {
    param([string]$InputFile)
    
    Write-Log "Importing environment variables..." -Level Info
    
    $root = Get-ProjectRoot
    $sourceFile = Join-Path $root $InputFile
    $destFile = Join-Path $root $File
    
    if (-not (Test-Path $sourceFile)) {
        Write-Log "Source file not found: $InputFile" -Level Error
        return
    }
    
    if ((Test-Path $destFile) -and (-not $Force)) {
        $continue = Confirm-Action "This will overwrite existing $File. Continue?"
        if (-not $continue) { return }
    }
    
    Copy-Item -Path $sourceFile -Destination $destFile -Force
    
    Write-Log "Imported from: $InputFile" -Level Success
}

# Main execution
switch ($Action) {
    "init" { Initialize-Environment }
    "set" { Set-EnvironmentVariable -VarName $Name -VarValue $Value }
    "get" { Get-EnvironmentVariable -VarName $Name }
    "list" { Get-EnvironmentList }
    "validate" { Test-EnvironmentVariables }
    "export" { Export-EnvironmentVariables -OutputFile $File }
    "import" { Import-EnvironmentVariables -InputFile $File }
    "help" { Show-Help }
}
