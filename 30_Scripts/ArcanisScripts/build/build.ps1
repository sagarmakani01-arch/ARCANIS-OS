# ArcanisScripts Build Automation
# Usage: .\build.ps1 [target] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("all", "clean", "compile", "bundle", "docker", "help")]
    [string]$Target = "all",
    
    [switch]$Clean,
    [switch]$Verbose,
    [switch]$Force,
    [string]$Configuration = "Release",
    [string]$OutputDir = ".\dist"
)

. "$PSScriptRoot\..\lib\common.ps1"

function Show-Help {
    Write-Host @"
ArcanisScripts Build Automation

Usage: .\build.ps1 [target] [options]

Targets:
    all         Build all targets (default)
    clean       Clean build artifacts
    compile     Compile source code
    bundle      Bundle for distribution
    docker      Build Docker image
    help        Show this help message

Options:
    -Clean          Clean before building
    -Verbose        Enable verbose output
    -Force          Skip confirmation prompts
    -Configuration  Build configuration (Debug/Release)
    -OutputDir      Output directory (default: .\dist)

Examples:
    .\build.ps1
    .\build.ps1 clean
    .\build.ps1 compile -Configuration Debug
    .\build.ps1 docker -Force
"@
}

function Invoke-Clean {
    Write-Log "Cleaning build artifacts..." -Level Info
    
    $directories = @(
        ".\dist",
        ".\build",
        ".\target",
        ".\node_modules\.cache",
        ".\.next"
    )
    
    foreach ($dir in $directories) {
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Write-Log "Removed: $dir" -Level Info
        }
    }
    
    Write-Log "Clean completed" -Level Success
}

function Invoke-Compile {
    Write-Log "Compiling source code..." -Level Info
    
    $root = Get-ProjectRoot
    
    # Detect project type and compile
    if (Test-Path "$root\package.json") {
        Write-Log "Detected Node.js project" -Level Info
        if (Test-Path "$root\tsconfig.json") {
            Invoke-SafeCommand "npm run build" "TypeScript compilation"
        } else {
            Invoke-SafeCommand "npm run build" "Node.js build"
        }
    }
    elseif (Test-Path "$root\Cargo.toml") {
        Write-Log "Detected Rust project" -Level Info
        $config = if ($Configuration -eq "Debug") { "--debug" } else { "--release" }
        Invoke-SafeCommand "cargo build $config" "Rust compilation"
    }
    elseif (Test-Path "$root\go.mod") {
        Write-Log "Detected Go project" -Level Info
        Invoke-SafeCommand "go build -o $OutputDir/app.exe" "Go compilation"
    }
    elseif (Test-Path "$root\*.csproj" -PathType Leaf) {
        Write-Log "Detected .NET project" -Level Info
        Invoke-SafeCommand "dotnet build -c $Configuration" ".NET compilation"
    }
    else {
        Write-Log "No recognized project type found" -Level Warning
    }
}

function Invoke-Bundle {
    Write-Log "Bundling for distribution..." -Level Info
    
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
    
    $root = Get-ProjectRoot
    $projectName = (Split-Path -Leaf $root)
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $bundleName = "${projectName}_${timestamp}"
    
    # Create bundle directory
    $bundlePath = Join-Path $OutputDir $bundleName
    New-Item -ItemType Directory -Path $bundlePath -Force | Out-Null
    
    # Copy artifacts
    $includePatterns = @(
        ".\dist\*",
        ".\build\*",
        ".\target\release\*",
        ".\*.exe",
        ".\*.dll",
        ".\*.json",
        ".\*.md"
    )
    
    foreach ($pattern in $includePatterns) {
        $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Copy-Item -Path $file.FullName -Destination $bundlePath -Recurse -Force
        }
    }
    
    # Create archive
    $archivePath = "$OutputDir\$bundleName.zip"
    Compress-Archive -Path "$bundlePath\*" -DestinationPath $archivePath -Force
    
    # Cleanup temp bundle
    Remove-Item -Recurse -Force $bundlePath
    
    Write-Log "Bundle created: $archivePath" -Level Success
}

function Invoke-DockerBuild {
    Write-Log "Building Docker image..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (-not (Test-Path "$root\Dockerfile")) {
        Write-Log "No Dockerfile found in project root" -Level Error
        return
    }
    
    $projectName = (Split-Path -Leaf $root).ToLower()
    $tag = "$projectName`:latest"
    
    Invoke-SafeCommand "docker build -t $tag ." "Docker build"
    Write-Log "Docker image built: $tag" -Level Success
}

# Main execution
switch ($Target) {
    "all" {
        if ($Clean) { Invoke-Clean }
        Invoke-Compile
        Invoke-Bundle
    }
    "clean" { Invoke-Clean }
    "compile" { Invoke-Compile }
    "bundle" { Invoke-Bundle }
    "docker" { Invoke-DockerBuild }
    "help" { Show-Help }
}
