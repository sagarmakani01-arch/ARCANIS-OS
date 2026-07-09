#!/usr/bin/env bash
# ArcanisScripts Backup Tools
# Usage: ./backup.sh [action] [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/common.sh"

ACTION="${1:-create}"
FORCE=false
VERBOSE=false
SOURCE="."
DESTINATION="./backups"
RETENTION="30d"

show_help() {
    cat << EOF
ArcanisScripts Backup Tools

Usage: ./backup.sh [action] [options]

Actions:
    create       Create a new backup (default)
    restore      Restore from a backup
    list         List available backups
    clean        Remove old backups
    help         Show this help message

Options:
    -f, --force           Skip confirmation prompts
    -v, --verbose         Enable verbose output
    -s, --source          Source directory to backup (default: .)
    -d, --destination     Backup destination directory (default: ./backups)
    -r, --retention       Retention period for backups (default: 30d)

Examples:
    ./backup.sh
    ./backup.sh create --source /path/to/project
    ./backup.sh restore --force
    ./backup.sh list
    ./backup.sh clean --retention "7d"
EOF
}

do_backup() {
    log_info "Creating backup..."
    
    local timestamp
    timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="backup_$timestamp"
    local backup_path="$DESTINATION/$backup_name"
    
    # Create backup directory
    mkdir -p "$DESTINATION"
    
    # Create backup
    mkdir -p "$backup_path"
    
    # Copy source files
    log_info "Copying files from $SOURCE..."
    
    # Use rsync if available for better performance
    if command_exists "rsync"; then
        local exclude_dirs=("node_modules" ".git" "dist" "build" "target" "__pycache__" ".venv")
        local exclude_args=""
        for dir in "${exclude_dirs[@]}"; do
            exclude_args="$exclude_args --exclude=$dir"
        done
        
        rsync -a $exclude_args "$SOURCE/" "$backup_path/"
    else
        # Fallback to cp
        find "$SOURCE" -maxdepth 1 -not -name "node_modules" -not -name ".git" -not -name "dist" -not -name "build" -exec cp -r {} "$backup_path/" \; 2>/dev/null || true
    fi
    
    # Create metadata file
    local file_count
    file_count=$(find "$backup_path" -type f | wc -l)
    local total_size
    total_size=$(du -sb "$backup_path" | cut -f1)
    
    cat > "$backup_path/backup.json" << EOF
{
    "timestamp": "$timestamp",
    "source": "$(realpath "$SOURCE")",
    "hostname": "$(hostname)",
    "username": "$(whoami)",
    "files": $file_count,
    "size": $total_size
}
EOF
    
    # Create archive
    local archive_path="$DESTINATION/$backup_name.tar.gz"
    log_info "Creating archive..."
    tar -czf "$archive_path" -C "$backup_path" .
    
    # Remove temporary backup directory
    rm -rf "$backup_path"
    
    log_success "Backup created: $archive_path"
    log_info "Size: $(du -h "$archive_path" | cut -f1)"
}

do_restore() {
    log_info "Restoring from backup..."
    
    # Find latest backup
    local latest_backup
    latest_backup=$(ls -t "$DESTINATION"/backup_*.tar.gz 2>/dev/null | head -n1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No backups found in $DESTINATION"
        return 1
    fi
    
    log_info "Restoring from: $(basename "$latest_backup")"
    
    if [ "$FORCE" = false ]; then
        if ! confirm_action "This will overwrite files in $SOURCE. Continue?"; then
            return 0
        fi
    fi
    
    # Extract archive
    local temp_path="/tmp/backup_restore_$(date '+%Y%m%d_%H%M%S')"
    mkdir -p "$temp_path"
    
    tar -xzf "$latest_backup" -C "$temp_path"
    
    # Copy files back
    cp -r "$temp_path/"* "$SOURCE/"
    
    # Cleanup
    rm -rf "$temp_path"
    
    log_success "Backup restored successfully"
}

do_list() {
    log_info "Available backups:"
    
    local backups
    backups=$(ls -lt "$DESTINATION"/backup_*.tar.gz 2>/dev/null)
    
    if [ -z "$backups" ]; then
        log_warning "No backups found"
        return 0
    fi
    
    echo ""
    echo "Date                    Size        Name"
    echo "------------------------------------------------------------"
    
    echo "$backups" | while read -r backup; do
        local size
        size=$(du -h "$backup" | cut -f1)
        local date
        date=$(stat -c '%y' "$backup" 2>/dev/null || stat -f '%Sm' "$backup" 2>/dev/null)
        local name
        name=$(basename "$backup")
        echo "$date    $size    $name"
    done
    
    local count
    count=$(ls "$DESTINATION"/backup_*.tar.gz 2>/dev/null | wc -l)
    echo ""
    log_info "Total: $count backup(s)"
}

do_clean() {
    log_info "Cleaning old backups..."
    
    # Parse retention period
    local days
    days=$(echo "$RETENTION" | grep -o '[0-9]*')
    local find_args=("-mtime" "+$days")
    
    local backups
    backups=$(find "$DESTINATION" -name "backup_*.tar.gz" -mtime "+$days" 2>/dev/null)
    
    if [ -z "$backups" ]; then
        log_info "No backups older than $RETENTION found"
        return 0
    fi
    
    local count
    count=$(echo "$backups" | wc -l)
    log_info "Found $count backup(s) older than $RETENTION"
    
    if [ "$FORCE" = false ]; then
        if ! confirm_action "Delete $count old backup(s)?"; then
            return 0
        fi
    fi
    
    echo "$backups" | while read -r backup; do
        rm -f "$backup"
        log_info "Removed: $(basename "$backup")"
    done
    
    log_success "Cleanup completed"
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
        -s|--source)
            SOURCE="$2"
            shift 2
            ;;
        -d|--destination)
            DESTINATION="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION="$2"
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
    create)
        do_backup
        ;;
    restore)
        do_restore
        ;;
    list)
        do_list
        ;;
    clean)
        do_clean
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
