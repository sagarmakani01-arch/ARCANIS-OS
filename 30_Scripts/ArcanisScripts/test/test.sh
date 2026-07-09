#!/usr/bin/env bash
# ArcanisScripts Testing Automation
# Usage: ./test.sh [action] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

ACTION="${1:-all}"
WATCH=false
VERBOSE=false
FORCE=false
FILTER=""
REPORT_FORMAT="html"

show_help() {
    cat << EOF
ArcanisScripts Testing Automation

Usage: ./test.sh [action] [options]

Actions:
    all          Run all tests (default)
    unit         Run unit tests only
    integration  Run integration tests only
    e2e          Run end-to-end tests only
    coverage     Generate coverage report
    lint         Run linter
    help         Show this help message

Options:
    -w, --watch           Watch mode for continuous testing
    -v, --verbose         Enable verbose output
    -f, --force           Skip confirmation prompts
    -F, --filter          Filter tests by name/pattern
    -r, --report          Coverage report format (html, json, xml)

Examples:
    ./test.sh
    ./test.sh unit
    ./test.sh coverage --report json
    ./test.sh e2e --filter "login"
    ./test.sh lint
EOF
}

do_unit_tests() {
    log_info "Running unit tests..."
    
    local root
    root=$(get_project_root)
    local watch_flag=""
    local filter_flag=""
    
    if [ "$WATCH" = true ]; then
        watch_flag="--watch"
    fi
    if [ -n "$FILTER" ]; then
        filter_flag="--filter $FILTER"
    fi
    
    if [ -f "$root/package.json" ]; then
        local scripts
        scripts=$(cat "$root/package.json" | grep -o '"test"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$scripts" ]; then
            invoke_safe_command "npm test $watch_flag $filter_flag" "Unit tests"
        else
            log_warning "No test script found in package.json"
        fi
    elif [ -f "$root/Cargo.toml" ]; then
        local filter_arg=""
        if [ -n "$FILTER" ]; then
            filter_arg="-- $FILTER"
        fi
        invoke_safe_command "cargo test $filter_arg" "Rust unit tests"
    elif [ -f "$root/go.mod" ]; then
        local filter_arg=""
        if [ -n "$FILTER" ]; then
            filter_arg="-run $FILTER"
        fi
        invoke_safe_command "go test ./... $filter_arg" "Go unit tests"
    elif ls "$root"/*.csproj 1> /dev/null 2>&1; then
        local filter_arg=""
        if [ -n "$FILTER" ]; then
            filter_arg="--filter $FILTER"
        fi
        invoke_safe_command "dotnet test $filter_arg" ".NET unit tests"
    else
        log_warning "No recognized project type found"
    fi
}

do_integration_tests() {
    log_info "Running integration tests..."
    
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        invoke_safe_command "npm run test:integration" "Integration tests"
    elif [ -f "$root/Cargo.toml" ]; then
        invoke_safe_command "cargo test --test '*' --features integration" "Rust integration tests"
    elif [ -f "$root/go.mod" ]; then
        invoke_safe_command "go test -tags=integration ./..." "Go integration tests"
    else
        log_warning "No recognized project type found"
    fi
}

do_e2e_tests() {
    log_info "Running end-to-end tests..."
    
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        if [ -d "$root/cypress" ]; then
            invoke_safe_command "npx cypress run" "Cypress E2E tests"
        elif ls "$root/playwright.config."* 1> /dev/null 2>&1; then
            invoke_safe_command "npx playwright test" "Playwright E2E tests"
        else
            invoke_safe_command "npm run test:e2e" "E2E tests"
        fi
    else
        log_warning "No E2E test framework detected"
    fi
}

do_coverage() {
    log_info "Generating coverage report..."
    
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        invoke_safe_command "npm run test:coverage" "Coverage report"
    elif [ -f "$root/Cargo.toml" ]; then
        if command_exists "cargo-tarpaulin"; then
            invoke_safe_command "cargo tarpaulin --out Html" "Rust coverage"
        else
            log_warning "cargo-tarpaulin not installed. Run: cargo install cargo-tarpaulin"
        fi
    elif [ -f "$root/go.mod" ]; then
        invoke_safe_command "go test -coverprofile=coverage.out ./..." "Go coverage"
        if [ "$REPORT_FORMAT" = "html" ]; then
            invoke_safe_command "go tool cover -html=coverage.out -o coverage.html" "Generate HTML report"
        fi
    else
        log_warning "No recognized project type found"
    fi
}

do_lint() {
    log_info "Running linter..."
    
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        if command_exists "eslint"; then
            invoke_safe_command "eslint ." "ESLint"
        else
            invoke_safe_command "npm run lint" "npm lint"
        fi
    elif [ -f "$root/Cargo.toml" ]; then
        if command_exists "cargo-clippy"; then
            invoke_safe_command "cargo clippy -- -D warnings" "Clippy"
        else
            log_warning "cargo-clippy not installed"
        fi
    elif [ -f "$root/go.mod" ]; then
        if command_exists "golangci-lint"; then
            invoke_safe_command "golangci-lint run" "golangci-lint"
        else
            invoke_safe_command "go vet ./..." "go vet"
        fi
    elif ls "$root"/*.csproj 1> /dev/null 2>&1; then
        if command_exists "dotnet-format"; then
            invoke_safe_command "dotnet-format --verify-no-changes" "dotnet format"
        fi
    else
        log_warning "No recognized project type found"
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--watch)
            WATCH=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -F|--filter)
            FILTER="$2"
            shift 2
            ;;
        -r|--report)
            REPORT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            ACTION="$1"
            shift
            ;;
    esac
done

# Main execution
case $ACTION in
    all)
        do_unit_tests
        do_integration_tests
        do_lint
        ;;
    unit)
        do_unit_tests
        ;;
    integration)
        do_integration_tests
        ;;
    e2e)
        do_e2e_tests
        ;;
    coverage)
        do_coverage
        ;;
    lint)
        do_lint
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown action: $ACTION"
        show_help
        exit 1
        ;;
esac
