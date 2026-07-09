# ArcanisScripts Testing Automation
# Usage: .\test.ps1 [action] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("all", "unit", "integration", "e2e", "coverage", "lint", "help")]
    [string]$Action = "all",
    
    [switch]$Watch,
    [switch]$Verbose,
    [switch]$Force,
    [string]$Filter = "",
    [string]$ReportFormat = "html"
)

. "$PSScriptRoot\..\lib\common.ps1"

function Show-Help {
    Write-Host @"
ArcanisScripts Testing Automation

Usage: .\test.ps1 [action] [options]

Actions:
    all          Run all tests (default)
    unit         Run unit tests only
    integration  Run integration tests only
    e2e          Run end-to-end tests only
    coverage     Generate coverage report
    lint         Run linter
    help         Show this help message

Options:
    -Watch           Watch mode for continuous testing
    -Verbose         Enable verbose output
    -Force           Skip confirmation prompts
    -Filter          Filter tests by name/pattern
    -ReportFormat    Coverage report format (html, json, xml)

Examples:
    .\test.ps1
    .\test.ps1 unit
    .\test.ps1 coverage -ReportFormat json
    .\test.ps1 e2e -Filter "login"
    .\test.ps1 lint
"@
}

function Invoke-UnitTests {
    Write-Log "Running unit tests..." -Level Info
    
    $root = Get-ProjectRoot
    $watchFlag = if ($Watch) { "--watch" } else { "" }
    $filterFlag = if ($Filter) { "--filter $Filter" } else { "" }
    
    if (Test-Path "$root\package.json") {
        $scripts = Get-Content "$root\package.json" | ConvertFrom-Json
        
        if ($scripts.scripts.test) {
            Invoke-SafeCommand "npm test $watchFlag $filterFlag" "Unit tests"
        } else {
            Write-Log "No test script found in package.json" -Level Warning
        }
    }
    elseif (Test-Path "$root\Cargo.toml") {
        $filterArg = if ($Filter) { "-- $Filter" } else { "" }
        Invoke-SafeCommand "cargo test $filterArg" "Rust unit tests"
    }
    elseif (Test-Path "$root\go.mod") {
        $filterArg = if ($Filter) { "-run $Filter" } else { "" }
        Invoke-SafeCommand "go test ./... $filterArg" "Go unit tests"
    }
    elseif (Test-Path "$root\*.csproj" -PathType Leaf) {
        $filterArg = if ($Filter) { "--filter $Filter" } else { "" }
        Invoke-SafeCommand "dotnet test $filterArg" ".NET unit tests"
    }
    else {
        Write-Log "No recognized project type found" -Level Warning
    }
}

function Invoke-IntegrationTests {
    Write-Log "Running integration tests..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        Invoke-SafeCommand "npm run test:integration" "Integration tests"
    }
    elseif (Test-Path "$root\Cargo.toml") {
        Invoke-SafeCommand "cargo test --test '*' --features integration" "Rust integration tests"
    }
    elseif (Test-Path "$root\go.mod") {
        Invoke-SafeCommand "go test -tags=integration ./..." "Go integration tests"
    }
    else {
        Write-Log "No recognized project type found" -Level Warning
    }
}

function Invoke-E2ETests {
    Write-Log "Running end-to-end tests..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        if (Test-Path "$root\cypress") {
            Invoke-SafeCommand "npx cypress run" "Cypress E2E tests"
        } elseif (Test-Path "$root\playwright.config.*") {
            Invoke-SafeCommand "npx playwright test" "Playwright E2E tests"
        } else {
            Invoke-SafeCommand "npm run test:e2e" "E2E tests"
        }
    }
    else {
        Write-Log "No E2E test framework detected" -Level Warning
    }
}

function Invoke-Coverage {
    Write-Log "Generating coverage report..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        Invoke-SafeCommand "npm run test:coverage" "Coverage report"
    }
    elseif (Test-Path "$root\Cargo.toml") {
        if (Test-CommandExists "cargo-tarpaulin") {
            Invoke-SafeCommand "cargo tarpaulin --out Html" "Rust coverage"
        } else {
            Write-Log "cargo-tarpaulin not installed. Run: cargo install cargo-tarpaulin" -Level Warning
        }
    }
    elseif (Test-Path "$root\go.mod") {
        Invoke-SafeCommand "go test -coverprofile=coverage.out ./..." "Go coverage"
        if ($ReportFormat -eq "html") {
            Invoke-SafeCommand "go tool cover -html=coverage.out -o coverage.html" "Generate HTML report"
        }
    }
    else {
        Write-Log "No recognized project type found" -Level Warning
    }
}

function Invoke-Lint {
    Write-Log "Running linter..." -Level Info
    
    $root = Get-ProjectRoot
    
    if (Test-Path "$root\package.json") {
        if (Test-CommandExists "eslint") {
            Invoke-SafeCommand "eslint ." "ESLint"
        } else {
            Invoke-SafeCommand "npm run lint" "npm lint"
        }
    }
    elseif (Test-Path "$root\Cargo.toml") {
        if (Test-CommandExists "cargo-clippy") {
            Invoke-SafeCommand "cargo clippy -- -D warnings" "Clippy"
        } else {
            Write-Log "cargo-clippy not installed" -Level Warning
        }
    }
    elseif (Test-Path "$root\go.mod") {
        if (Test-CommandExists "golangci-lint") {
            Invoke-SafeCommand "golangci-lint run" "golangci-lint"
        } else {
            Invoke-SafeCommand "go vet ./..." "go vet"
        }
    }
    elseif (Test-Path "$root\*.csproj" -PathType Leaf) {
        if (Test-CommandExists "dotnet-format") {
            Invoke-SafeCommand "dotnet-format --verify-no-changes" "dotnet format"
        }
    }
    else {
        Write-Log "No recognized project type found" -Level Warning
    }
}

# Main execution
switch ($Action) {
    "all" {
        Invoke-UnitTests
        Invoke-IntegrationTests
        Invoke-Lint
    }
    "unit" { Invoke-UnitTests }
    "integration" { Invoke-IntegrationTests }
    "e2e" { Invoke-E2ETests }
    "coverage" { Invoke-Coverage }
    "lint" { Invoke-Lint }
    "help" { Show-Help }
}
