#!/usr/bin/env bash
# ArcanisScripts Deployment Automation
# Usage: ./deploy.sh [environment] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

ENVIRONMENT="${1:-staging}"
DRY_RUN=false
FORCE=false
SKIP_TESTS=false
VERBOSE=false
VERSION=""

show_help() {
    cat << EOF
ArcanisScripts Deployment Automation

Usage: ./deploy.sh [environment] [options]

Environments:
    staging      Deploy to staging environment (default)
    production   Deploy to production environment
    preview      Deploy to preview environment
    rollback     Rollback to previous version
    help         Show this help message

Options:
    -d, --dry-run          Simulate deployment without executing
    -f, --force           Skip confirmation prompts
    -s, --skip-tests      Skip running tests before deployment
    -v, --verbose         Enable verbose output
    -V, --version         Specific version to deploy

Examples:
    ./deploy.sh
    ./deploy.sh production
    ./deploy.sh staging --dry-run
    ./deploy.sh production --version "1.2.3" --force
    ./deploy.sh rollback
EOF
}

test_deployment_prerequisites() {
    log_info "Checking deployment prerequisites..."
    
    local root
    root=$(get_project_root)
    
    # Check for required tools
    if ! test_dependencies git; then
        return 1
    fi
    
    # Check for clean working directory
    local status
    status=$(git status --porcelain)
    if [ -n "$status" ]; then
        log_error "Working directory is not clean. Commit or stash changes first."
        return 1
    fi
    
    # Check for unpushed commits
    local unpushed
    unpushed=$(git log @{upstream}..HEAD --oneline 2>/dev/null || true)
    if [ -n "$unpushed" ]; then
        log_warning "You have unpushed commits. Push before deploying."
        if [ "$FORCE" = false ]; then
            if ! confirm_action "Continue anyway?"; then
                return 1
            fi
        fi
    fi
    
    return 0
}

get_current_version() {
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$root/package.json" | cut -d'"' -f4
    elif [ -f "$root/Cargo.toml" ]; then
        grep -o 'version[[:space:]]*=[[:space:]]*"[^"]*"' "$root/Cargo.toml" | cut -d'"' -f2
    else
        echo "0.0.0"
    fi
}

run_pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    if [ "$SKIP_TESTS" = false ]; then
        log_info "Running tests before deployment..."
        local test_script="$SCRIPT_DIR/../test/test.sh"
        if [ -f "$test_script" ]; then
            bash "$test_script" unit
            if [ $? -ne 0 ]; then
                log_error "Tests failed. Deployment aborted."
                return 1
            fi
        fi
    fi
    
    return 0
}

do_deploy() {
    local env="$1"
    local ver="$2"
    local root
    root=$(get_project_root)
    
    log_info "Deploying to $env..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would deploy to $env"
        return 0
    fi
    
    # Deploy based on project type
    if [ -f "$root/package.json" ]; then
        if grep -q '"vercel"' "$root/package.json" 2>/dev/null; then
            local prod_flag=""
            if [ "$env" = "production" ]; then
                prod_flag="--prod"
            fi
            invoke_safe_command "vercel deploy $prod_flag --yes" "Vercel deployment"
        elif grep -q '"aws-sdk"' "$root/package.json" 2>/dev/null; then
            invoke_safe_command "aws s3 sync ./dist s3://$env-bucket" "AWS S3 deployment"
        else
            log_warning "No deployment provider detected"
        fi
    elif [ -f "$root/Dockerfile" ]; then
        local registry="ghcr.io"
        local project_name
        project_name=$(basename "$root" | tr '[:upper:]' '[:lower:]')
        local tag="$registry/$project_name:$ver"
        
        invoke_safe_command "docker tag $project_name:latest $tag" "Tag Docker image"
        invoke_safe_command "docker push $tag" "Push Docker image"
    fi
    
    log_success "Deployment to $env completed!"
    return 0
}

do_rollback() {
    log_info "Rolling back to previous version..."
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would rollback"
        return 0
    fi
    
    # Get last commit hash
    local last_commit
    last_commit=$(git rev-parse HEAD~1)
    
    if confirm_action "Rollback to commit $last_commit?" "$FORCE"; then
        invoke_safe_command "git checkout $last_commit" "Checkout previous commit"
        invoke_safe_command "git commit -m 'Rollback to $last_commit'" "Create rollback commit"
        log_success "Rollback completed"
    fi
    
    return 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -V|--version)
            VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            ENVIRONMENT="$1"
            shift
            ;;
    esac
done

# Main execution
log_info "ArcanisScripts Deployment"
log_info "Environment: $ENVIRONMENT"
log_info "Version: $(if [ -n "$VERSION" ]; then echo "$VERSION"; else get_current_version; fi)"

if [ "$ENVIRONMENT" = "help" ]; then
    show_help
    exit 0
fi

if [ "$FORCE" = false ]; then
    if ! confirm_action "Deploy to $ENVIRONMENT?"; then
        log_warning "Deployment cancelled"
        exit 0
    fi
fi

if [ "$ENVIRONMENT" = "rollback" ]; then
    do_rollback
    exit $?
fi

if ! test_deployment_prerequisites; then
    exit 1
fi

if ! run_pre_deployment_checks; then
    exit 1
fi

do_deploy "$ENVIRONMENT" "$(if [ -n "$VERSION" ]; then echo "$VERSION"; else get_current_version; fi)"
