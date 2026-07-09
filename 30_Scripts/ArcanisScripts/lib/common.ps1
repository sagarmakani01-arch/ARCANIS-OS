# ArcanisScripts Common Utilities
# Cross-platform helper functions for all scripts

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSScriptRoot

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("Info", "Warning", "Error", "Success")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "Info"    { "Cyan" }
        "Warning" { "Yellow" }
        "Error"   { "Red" }
        "Success" { "Green" }
    }
    
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-CommandExists {
    param([string]$Command)
    
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    
    try {
        if (Get-Command $Command -erroraction SilentlyContinue) {
            return $true
        }
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $oldPreference
    }
}

function Get-ProjectRoot {
    param([string]$StartPath = $PWD)
    
    $current = $StartPath
    while ($current -ne $null) {
        if (Test-Path "$current\.git" -PathType Container) {
            return $current
        }
        if (Test-Path "$current\package.json" -PathType Leaf) {
            return $current
        }
        if (Test-Path "$current\Cargo.toml" -PathType Leaf) {
            return $current
        }
        if (Test-Path "$current\go.mod" -PathType Leaf) {
            return $current
        }
        $current = Split-Path -Parent $current
    }
    return $StartPath
}

function Invoke-SafeCommand {
    param(
        [string]$Command,
        [string]$Description,
        [switch]$ContinueOnError
    )
    
    Write-Log "Executing: $Description" -Level Info
    Write-Log "Command: $Command" -Level Info
    
    try {
        Invoke-Expression $Command
        Write-Log "Completed: $Description" -Level Success
        return $true
    } catch {
        if ($ContinueOnError) {
            Write-Log "Failed: $Description - $($_.Exception.Message)" -Level Warning
            return $false
        } else {
            Write-Log "Failed: $Description - $($_.Exception.Message)" -Level Error
            throw
        }
    }
}

function Confirm-Action {
    param(
        [string]$Message,
        [switch]$Force
    )
    
    if ($Force) { return $true }
    
    $response = Read-Host "$Message (y/N)"
    return ($response -eq 'y' -or $response -eq 'Y')
}

function Get-ScriptDirectory {
    return Split-Path -Parent $MyInvocation.PSCommandPath
}

function Test-Dependencies {
    param([string[]]$Dependencies)
    
    $missing = @()
    foreach ($dep in $Dependencies) {
        if (-not (Test-CommandExists $dep)) {
            $missing += $dep
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Log "Missing dependencies: $($missing -join ', ')" -Level Error
        return $false
    }
    return $true
}

Export-ModuleMember -Function Write-Log, Test-CommandExists, Get-ProjectRoot, Invoke-SafeCommand, Confirm-Action, Get-ScriptDirectory, Test-Dependencies
