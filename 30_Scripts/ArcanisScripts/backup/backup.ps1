# ArcanisScripts Backup Tools
# Usage: .\backup.ps1 [action] [options]

param(
    [Parameter(Position=0)]
    [ValidateSet("create", "restore", "list", "clean", "help")]
    [string]$Action = "create",
    
    [switch]$Force,
    [switch]$Verbose,
    [string]$Source = ".",
    [string]$Destination = ".\backups",
    [string]$Retention = "30d"
)

. "$PSScriptRoot\..\lib\common.ps1"

function Show-Help {
    Write-Host @"
ArcanisScripts Backup Tools

Usage: .\backup.ps1 [action] [options]

Actions:
    create       Create a new backup (default)
    restore      Restore from a backup
    list         List available backups
    clean        Remove old backups
    help         Show this help message

Options:
    -Force           Skip confirmation prompts
    -Verbose         Enable verbose output
    -Source          Source directory to backup (default: .)
    -Destination     Backup destination directory (default: .\backups)
    -Retention       Retention period for backups (default: 30d)

Examples:
    .\backup.ps1
    .\backup.ps1 create -Source "C:\MyProject"
    .\backup.ps1 restore -Force
    .\backup.ps1 list
    .\backup.ps1 clean -Retention "7d"
"@
}

function New-Backup {
    Write-Log "Creating backup..." -Level Info
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "backup_$timestamp"
    $backupPath = Join-Path $Destination $backupName
    
    # Create backup directory
    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    
    # Create backup
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    
    # Copy source files
    Write-Log "Copying files from $Source..." -Level Info
    $sourcePath = (Resolve-Path $Source).Path
    
    # Use robocopy on Windows for better performance
    if (Get-Command "robocopy" -ErrorAction SilentlyContinue) {
        $excludeDirs = @("node_modules", ".git", "dist", "build", "target", "__pycache__", ".venv")
        $excludeArg = ($excludeDirs | ForEach-Object { "/XD $_" }) -join " "
        
        Invoke-SafeCommand "robocopy `"$sourcePath`" `"$backupPath`" /E /MT /R:3 /W:1 $excludeArg /NFL /NDL /NJH /NJS" "Robocopy backup"
    } else {
        # Fallback to PowerShell Copy-Item
        Get-ChildItem -Path $sourcePath -Exclude "node_modules", ".git", "dist", "build" | 
            Copy-Item -Destination $backupPath -Recurse -Force
    }
    
    # Create metadata file
    $metadata = @{
        timestamp = $timestamp
        source = $sourcePath
        hostname = $env:COMPUTERNAME
        username = $env:USERNAME
        files = (Get-ChildItem -Path $backupPath -Recurse -File).Count
        size = (Get-ChildItem -Path $backupPath -Recurse -File | Measure-Object -Property Length -Sum).Sum
    }
    
    $metadata | ConvertTo-Json | Out-File -FilePath "$backupPath\backup.json" -Encoding UTF8
    
    # Create archive
    $archivePath = "$Destination\$backupName.zip"
    Write-Log "Creating archive..." -Level Info
    Compress-Archive -Path "$backupPath\*" -DestinationPath $archivePath -Force
    
    # Remove temporary backup directory
    Remove-Item -Recurse -Force $backupPath
    
    Write-Log "Backup created: $archivePath" -Level Success
    Write-Log "Size: $([math]::Round((Get-Item $archivePath).Length / 1MB, 2)) MB" -Level Info
}

function Restore-Backup {
    Write-Log "Restoring from backup..." -Level Info
    
    # Find latest backup
    $backups = Get-ChildItem -Path $Destination -Filter "backup_*.zip" | Sort-Object LastWriteTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Log "No backups found in $Destination" -Level Error
        return
    }
    
    $latestBackup = $backups[0]
    Write-Log "Restoring from: $($latestBackup.Name)" -Level Info
    
    if (-not $Force) {
        $continue = Confirm-Action "This will overwrite files in $Source. Continue?"
        if (-not $continue) { return }
    }
    
    # Extract archive
    $tempPath = Join-Path $env:TEMP "backup_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $tempPath -Force | Out-Null
    
    Expand-Archive -Path $latestBackup.FullName -DestinationPath $tempPath -Force
    
    # Copy files back
    Copy-Item -Path "$tempPath\*" -Destination $Source -Recurse -Force
    
    # Cleanup
    Remove-Item -Recurse -Force $tempPath
    
    Write-Log "Backup restored successfully" -Level Success
}

function Get-BackupList {
    Write-Log "Available backups:" -Level Info
    
    $backups = Get-ChildItem -Path $Destination -Filter "backup_*.zip" | Sort-Object LastWriteTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Log "No backups found" -Level Warning
        return
    }
    
    Write-Host "`nDate                    Size        Name"
    Write-Host "-" * 60
    
    foreach ($backup in $backups) {
        $size = [math]::Round($backup.Length / 1MB, 2)
        $date = $backup.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "$date    $($size.ToString("N2")) MB    $($backup.Name)"
    }
    
    Write-Host "`nTotal: $($backups.Count) backup(s)" -Level Info
}

function Remove-OldBackups {
    Write-Log "Cleaning old backups..." -Level Info
    
    # Parse retention period
    $days = [int]($Retention -replace '[^0-9]', '')
    $cutoffDate = (Get-Date).AddDays(-$days)
    
    $backups = Get-ChildItem -Path $Destination -Filter "backup_*.zip" | 
        Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    if ($backups.Count -eq 0) {
        Write-Log "No backups older than $Retention found" -Level Info
        return
    }
    
    Write-Log "Found $($backups.Count) backup(s) older than $Retention" -Level Info
    
    if (-not $Force) {
        $continue = Confirm-Action "Delete $($backups.Count) old backup(s)?"
        if (-not $continue) { return }
    }
    
    foreach ($backup in $backups) {
        Remove-Item -Path $backup.FullName -Force
        Write-Log "Removed: $($backup.Name)" -Level Info
    }
    
    Write-Log "Cleanup completed" -Level Success
}

# Main execution
switch ($Action) {
    "create" { New-Backup }
    "restore" { Restore-Backup }
    "list" { Get-BackupList }
    "clean" { Remove-OldBackups }
    "help" { Show-Help }
}
