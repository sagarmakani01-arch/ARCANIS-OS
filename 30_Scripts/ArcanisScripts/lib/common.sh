#!/usr/bin/env bash
# ArcanisScripts Common Utilities
# Cross-platform helper functions for all scripts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${CYAN}[$timestamp] [Info] $1${NC}"
}

log_warning() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[$timestamp] [Warning] $1${NC}"
}

log_error() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[$timestamp] [Error] $1${NC}"
}

log_success() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[$timestamp] [Success] $1${NC}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

get_project_root() {
    local start_path="${1:-$PWD}"
    local current="$start_path"
    
    while [ "$current" != "/" ]; do
        if [ -d "$current/.git" ]; then
            echo "$current"
            return 0
        fi
        if [ -f "$current/package.json" ]; then
            echo "$current"
            return 0
        fi
        if [ -f "$current/Cargo.toml" ]; then
            echo "$current"
            return 0
        fi
        if [ -f "$current/go.mod" ]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    echo "$start_path"
}

invoke_safe_command() {
    local command="$1"
    local description="$2"
    local continue_on_error="${3:-false}"
    
    log_info "Executing: $description"
    log_info "Command: $command"
    
    if eval "$command"; then
        log_success "Completed: $description"
        return 0
    else
        if [ "$continue_on_error" = "true" ]; then
            log_warning "Failed: $description"
            return 1
        else
            log_error "Failed: $description"
            return 1
        fi
    fi
}

confirm_action() {
    local message="$1"
    local force="${2:-false}"
    
    if [ "$force" = "true" ]; then
        return 0
    fi
    
    read -p "$message (y/N): " response
    [[ "$response" =~ ^[Yy]$ ]]
}

test_dependencies() {
    local missing=()
    
    for dep in "$@"; do
        if ! command_exists "$dep"; then
            missing+=("$dep")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        return 1
    fi
    return 0
}

get_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

export -f log_info log_warning log_error log_success
export -f command_exists get_project_root invoke_safe_command
export -f confirm_action test_dependencies get_os
export SCRIPT_DIR SCRIPT_ROOT
export RED GREEN YELLOW BLUE CYAN NC
