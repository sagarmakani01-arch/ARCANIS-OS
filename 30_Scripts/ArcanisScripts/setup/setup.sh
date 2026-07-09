#!/usr/bin/env bash
# ArcanisScripts Setup Automation
# Usage: ./setup.sh [action] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

ACTION="${1:-init}"
FORCE=false
VERBOSE=false
PROJECT_TYPE="node"
PROJECT_NAME="my-project"

show_help() {
    cat << EOF
ArcanisScripts Setup Automation

Usage: ./setup.sh [action] [options]

Actions:
    init         Initialize a new project (default)
    install      Install dependencies
    update       Update dependencies
    reset        Reset project to clean state
    help         Show this help message

Options:
    -f, --force           Skip confirmation prompts
    -v, --verbose         Enable verbose output
    -t, --type            Project type (node, rust, go, dotnet, python)
    -n, --name            Name for new project

Examples:
    ./setup.sh init --type node --name "my-app"
    ./setup.sh install
    ./setup.sh update
    ./setup.sh reset --force
EOF
}

init_project() {
    log_info "Initializing new project: $PROJECT_NAME"
    
    if [ -d "$PROJECT_NAME" ]; then
        if [ "$FORCE" = false ]; then
            if ! confirm_action "Directory '$PROJECT_NAME' exists. Overwrite?"; then
                return 0
            fi
        fi
        rm -rf "$PROJECT_NAME"
    fi
    
    mkdir -p "$PROJECT_NAME"
    
    case $PROJECT_TYPE in
        node)
            log_info "Creating Node.js project..."
            cd "$PROJECT_NAME"
            invoke_safe_command "npm init -y" "Initialize npm"
            invoke_safe_command "npm install typescript @types/node --save-dev" "Install TypeScript"
            invoke_safe_command "npx tsc --init" "Initialize TypeScript"
            cd ..
            ;;
        rust)
            log_info "Creating Rust project..."
            invoke_safe_command "cargo new $PROJECT_NAME" "Initialize Cargo project"
            ;;
        go)
            log_info "Creating Go project..."
            cd "$PROJECT_NAME"
            local module_path="github.com/username/$PROJECT_NAME"
            invoke_safe_command "go mod init $module_path" "Initialize Go module"
            cd ..
            ;;
        dotnet)
            log_info "Creating .NET project..."
            invoke_safe_command "dotnet new console -n $PROJECT_NAME" "Initialize .NET project"
            ;;
        python)
            log_info "Creating Python project..."
            cd "$PROJECT_NAME"
            cat > pyproject.toml << EOF
[project]
name = "$PROJECT_NAME"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.8"
EOF
            mkdir -p src tests
            cd ..
            ;;
    esac
    
    # Create common files
    cd "$PROJECT_NAME"
    
    cat > README.md << EOF
# $PROJECT_NAME

## Description
Brief description of your project.

## Installation
\`\`\`bash
# Add installation instructions here
\`\`\`

## Usage
\`\`\`bash
# Add usage examples here
\`\`\`

## License
MIT
EOF
    
    cat > .gitignore << EOF
node_modules/
dist/
build/
.env
.env.local
*.log
.DS_Store
Thumbs.db
EOF
    
    cd ..
    
    log_success "Project '$PROJECT_NAME' created successfully!"
}

install_dependencies() {
    log_info "Installing dependencies..."
    
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        invoke_safe_command "npm install" "Install npm dependencies"
    elif [ -f "$root/Cargo.toml" ]; then
        invoke_safe_command "cargo fetch" "Fetch Rust dependencies"
    elif [ -f "$root/go.mod" ]; then
        invoke_safe_command "go mod download" "Download Go modules"
    elif ls "$root"/*.csproj 1> /dev/null 2>&1; then
        invoke_safe_command "dotnet restore" "Restore .NET packages"
    elif [ -f "$root/requirements.txt" ]; then
        invoke_safe_command "pip install -r requirements.txt" "Install Python packages"
    elif [ -f "$root/pyproject.toml" ]; then
        invoke_safe_command "pip install -e ." "Install Python package"
    else
        log_warning "No dependency file found"
    fi
}

update_dependencies() {
    log_info "Updating dependencies..."
    
    local root
    root=$(get_project_root)
    
    if [ -f "$root/package.json" ]; then
        invoke_safe_command "npm update" "Update npm packages"
        invoke_safe_command "npm audit fix" "Fix security vulnerabilities"
    elif [ -f "$root/Cargo.toml" ]; then
        invoke_safe_command "cargo update" "Update Cargo packages"
    elif [ -f "$root/go.mod" ]; then
        invoke_safe_command "go get -u ./..." "Update Go modules"
        invoke_safe_command "go mod tidy" "Tidy Go modules"
    elif ls "$root"/*.csproj 1> /dev/null 2>&1; then
        invoke_safe_command "dotnet list package --outdated" "Check for updates"
    elif [ -f "$root/requirements.txt" ]; then
        log_info "For Python, consider using: pip install --upgrade -r requirements.txt"
    fi
}

reset_project() {
    log_info "Resetting project..."
    
    local root
    root=$(get_project_root)
    
    if [ "$FORCE" = false ]; then
        if ! confirm_action "This will remove all untracked files and reset changes. Continue?"; then
            return 0
        fi
    fi
    
    # Clean build artifacts
    bash "$SCRIPT_DIR/../build/build.sh" clean
    
    # Reset git if in a repo
    if [ -d "$root/.git" ]; then
        cd "$root"
        invoke_safe_command "git clean -fd" "Remove untracked files"
        invoke_safe_command "git checkout -- ." "Reset changes"
        cd ..
    fi
    
    # Reinstall dependencies
    install_dependencies
    
    log_success "Project reset completed"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--type)
            PROJECT_TYPE="$2"
            shift 2
            ;;
        -n|--name)
            PROJECT_NAME="$2"
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
    init)
        init_project
        ;;
    install)
        install_dependencies
        ;;
    update)
        update_dependencies
        ;;
    reset)
        reset_project
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
