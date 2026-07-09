# ArcanisScripts Deployment Automation
# Usage: .\deploy.ps1 [environment] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("staging", "production", "preview", "rollback", "help")]
    [string]$Environment = "staging",
    
    [switch]$DryRun,
    [switch]$Force,
    [switch]$SkipTests,
    [switch]$Verbose,
    [string]$Version = ""
)

. "$PSScriptRoot\..\lib\common.ps1"

function Show-Help {
    Write-Host @"
ArcanisScripts Deployment Automation

Usage: .\deploy.ps1 [environment] [options]

Environments:
    staging      Deploy to staging environment (default)
    production   Deploy to production environment
    preview      Deploy to preview environment
    rollback     Rollback to previous version
    help         Show this help message

Options:
    -DryRun          Simulate deployment without executing
    -Force           Skip confirmation prompts
    -SkipTests       Skip running tests before deployment
    -Verbose         Enable verbose output
    -Version         Specific version to deploy

Examples:
    .\deploy.ps1
    .\deploy.ps1 production
    .\deploy.ps1 staging -DryRun
    .\deploy.ps1 production -Version "1.2.3" -Force
    .\deploy.ps1 rollback
"@
}

function Test-DeploymentPrerequisites {
    Write-Log "Checking deployment prerequisites..." -Level Info
    
    $root = Get-ProjectRoot
    
    # Check for required tools
    $requiredTools = @("git")
    if (-not (Test-Dependencies $requiredTools)) {
        return $false
    }
    
    # Check for clean working directory
    $status = git status --porcelain
    if ($status) {
        Write-Log "Working directory is not clean. Commit or stash changes first." -Level Error
        return $false
    }
    
    # Check for unpushed commits
    $unpushed = git log @{upstream}..HEAD --oneline 2>$null
    if ($unpushed) {
        Write-Log "You have unpushed commits. Push before deploying." -Level Warning
        if (-not $Force) {
            $continue = Confirm-Action "Continue anyway?"
            if (-not $continue) { return $false }
        }
    }
    
    return $true
}

function Get-CurrentVersion {
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        $pkg = Get-Content "$root\package.json" | ConvertFrom-Json
        return $pkg.version
    }
    elseif (Test-Path "$root\Cargo.toml") {
        $content = Get-Content "$root\Cargo.toml" | Select-String 'version\s*=\s*"([^"]+)"'
        if ($content -match '"([^"]+)"') {
            return $matches[1]
        }
    }
    
    return "0.0.0"
}

function Invoke-PreDeploymentChecks {
    Write-Log "Running pre-deployment checks..." -Level Info
    
    if (-not $SkipTests) {
        Write-Log "Running tests before deployment..." -Level Info
        $testScript = "$PSScriptRoot\..\test\test.ps1"
        if (Test-Path $testScript) {
            & $testScript unit
            if ($LASTEXITCODE -ne 0) {
                Write-Log "Tests failed. Deployment aborted." -Level Error
                return $false
            }
        }
    }
    
    return $true
}

function Invoke-Deployment {
    param(
        [string]$Env,
        [string]$Ver
    )
    
    $root = Get-ProjectRoot
    $deployConfig = "$root\.deploy.json"
    
    if (Test-Path $deployConfig) {
        $config = Get-Content $deployConfig | ConvertFrom-Json
    } else {
        # Default deployment configuration
        $config = @{
            staging = @{
                url = "https://staging.example.com"
                provider = "vercel"
            }
            production = @{
                url = "https://example.com"
                provider = "vercel"
            }
        }
    }
    
    Write-Log "Deploying to $Env..." -Level Info
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would deploy to $Env" -Level Warning
        return $true
    }
    
    # Deploy based on project type
    if (Test-Path "$root\package.json") {
        $pkg = Get-Content "$root\package.json" | ConvertFrom-Json
        
        if ($pkg.dependencies.vercel -or $pkg.devDependencies.vercel) {
            $prodFlag = if ($Env -eq "production") { "--prod" } else { "" }
            Invoke-SafeCommand "vercel deploy $prodFlag --yes" "Vercel deployment"
        }
        elseif ($pkg.dependencies."aws-sdk" -or $pkg.devDependencies."aws-sdk") {
            Invoke-SafeCommand "aws s3 sync ./dist s3://$Env-bucket" "AWS S3 deployment"
        }
        else {
            Write-Log "No deployment provider detected" -Level Warning
        }
    }
    elseif (Test-Path "$root\Dockerfile") {
        $registry = "ghcr.io"
        $projectName = (Split-Path -Leaf $root).ToLower()
        $tag = "$registry/$projectName`:$Ver"
        
        Invoke-SafeCommand "docker tag $projectName`:latest $tag" "Tag Docker image"
        Invoke-SafeCommand "docker push $tag" "Push Docker image"
    }
    
    Write-Log "Deployment to $Env completed!" -Level Success
    return $true
}

function Invoke-Rollback {
    Write-Log "Rolling back to previous version..." -Level Info
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would rollback" -Level Warning
        return $true
    }
    
    # Get last commit hash
    $lastCommit = git rev-parse HEAD~1
    
    if (Confirm-Action "Rollback to commit $lastCommit?" -Force $Force) {
        Invoke-SafeCommand "git checkout $lastCommit" "Checkout previous commit"
        Invoke-SafeCommand "git commit -m 'Rollback to $lastCommit'" "Create rollback commit"
        Write-Log "Rollback completed" -Level Success
    }
    
    return $true
}

# Main execution
Write-Log "ArcanisScripts Deployment" -Level Info
Write-Log "Environment: $Environment" -Level Info
Write-Log "Version: $(if ($Version) { $Version } else { Get-CurrentVersion })" -Level Info

if ($Environment -eq "help") {
    Show-Help
    exit 0
}

if (-not $Force) {
    $continue = Confirm-Action "Deploy to $Environment?"
    if (-not $continue) {
        Write-Log "Deployment cancelled" -Level Warning
        exit 0
    }
}

if ($Environment -eq "rollback") {
    Invoke-Rollback
    exit 0
}

if (-not (Test-DeploymentPrerequisites)) {
    exit 1
}

if (-not (Invoke-PreDeploymentChecks)) {
    exit 1
}

Invoke-Deployment -Env $Environment -Ver $(if ($Version) { $Version } else { Get-CurrentVersion })
