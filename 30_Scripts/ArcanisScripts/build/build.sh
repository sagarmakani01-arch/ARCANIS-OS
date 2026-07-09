#!/usr/bin/env bash
# ArcanisScripts Build Automation
# Usage: ./build.sh [target] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

TARGET="${1:-all}"
CLEAN=false
VERBOSE=false
FORCE=false
CONFIGURATION="Release"
OUTPUT_DIR="./dist"

show_help() {
    cat << EOF
ArcanisScripts Build Automation

Usage: ./build.sh [target] [options]

Targets:
    all         Build all targets (default)
    clean       Clean build artifacts
    compile     Compile source code
    bundle      Bundle for distribution
    docker      Build Docker image
    help        Show this help message

Options:
    -c, --clean          Clean before building
    -v, --verbose        Enable verbose output
    -f, --force          Skip confirmation prompts
    -C, --config         Build configuration (Debug/Release)
    -o, --output         Output directory (default: ./dist)

Examples:
    ./build.sh
    ./build.sh clean
    ./build.sh compile --config Debug
    ./build.sh docker --force
EOF
}

do_clean() {
    log_info "Cleaning build artifacts..."
    
    local directories=(
        "./dist"
        "./build"
        "./target"
        "./node_modules/.cache"
        "./.next"
    )
    
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log_info "Removed: $dir"
        fi
    done
    
    log_success "Clean completed"
}

do_compile() {
    log_info "Compiling source code..."
    
    local root
    root=$(get_project_root)
    
    # Detect project type and compile
    if [ -f "$root/package.json" ]; then
        log_info "Detected Node.js project"
        if [ -f "$root/tsconfig.json" ]; then
            invoke_safe_command "npm run build" "TypeScript compilation"
        else
            invoke_safe_command "npm run build" "Node.js build"
        fi
    elif [ -f "$root/Cargo.toml" ]; then
        log_info "Detected Rust project"
        local config_flag=""
        if [ "$CONFIGURATION" = "Debug" ]; then
            config_flag="--debug"
        else
            config_flag="--release"
        fi
        invoke_safe_command "cargo build $config_flag" "Rust compilation"
    elif [ -f "$root/go.mod" ]; then
        log_info "Detected Go project"
        invoke_safe_command "go build -o $OUTPUT_DIR/app" "Go compilation"
    elif ls "$root"/*.csproj 1> /dev/null 2>&1; then
        log_info "Detected .NET project"
        invoke_safe_command "dotnet build -c $CONFIGURATION" ".NET compilation"
    else
        log_warning "No recognized project type found"
    fi
}

do_bundle() {
    log_info "Bundling for distribution..."
    
    if [ ! -d "$OUTPUT_DIR" ]; then
        mkdir -p "$OUTPUT_DIR"
    fi
    
    local root
    root=$(get_project_root)
    local project_name
    project_name=$(basename "$root")
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local bundle_name="${project_name}_${timestamp}"
    
    # Create bundle directory
    local bundle_path="$OUTPUT_DIR/$bundle_name"
    mkdir -p "$bundle_path"
    
    # Copy artifacts
    local include_patterns=(
        "./dist/*"
        "./build/*"
        "./target/release/*"
        "./*.exe"
        "./*.dll"
        "./*.json"
        "./*.md"
    )
    
    for pattern in "${include_patterns[@]}"; do
        # Use compgen to handle glob patterns safely
        if compgen -G "$pattern" > /dev/null 2>&1; then
            cp -r $pattern "$bundle_path/" 2>/dev/null || true
        fi
    done
    
    # Create archive
    local archive_path="$OUTPUT_DIR/$bundle_name.tar.gz"
    tar -czf "$archive_path" -C "$bundle_path" .
    
    # Cleanup temp bundle
    rm -rf "$bundle_path"
    
    log_success "Bundle created: $archive_path"
}

do_docker() {
    log_info "Building Docker image..."
    
    local root
    root=$(get_project_root)
    
    if [ ! -f "$root/Dockerfile" ]; then
        log_error "No Dockerfile found in project root"
        return 1
    fi
    
    local project_name
    project_name=$(basename "$root" | tr '[:upper:]' '[:lower:]')
    local tag="${project_name}:latest"
    
    invoke_safe_command "docker build -t $tag ." "Docker build"
    log_success "Docker image built: $tag"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            CLEAN=true
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
        -C|--config)
            CONFIGURATION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# Main execution
case $TARGET in
    all)
        if [ "$CLEAN" = true ]; then
            do_clean
        fi
        do_compile
        do_bundle
        ;;
    clean)
        do_clean
        ;;
    compile)
        do_compile
        ;;
    bundle)
        do_bundle
        ;;
    docker)
        do_docker
        ;;
    help)
        show_help
        ;;
    *)
        log_error "Unknown target: $TARGET"
        show_help
        exit 1
        ;;
esac
