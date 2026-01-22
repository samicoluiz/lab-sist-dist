# -*- coding: utf-8 -*-
# PowerShell script to stop and clean the distributed environment

# --- Configuration Variables ---
$PidFile = "node_pids.tmp"
$LogDir = "logs"

# --- Helper Functions ---

function Log-Message {
    Param (
        [string]$Message
    )
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
}

function Check-Command {
    Param (
        [string]$Command
    )
    (Get-Command $Command -ErrorAction SilentlyContinue) -ne $null
}

# --- Script Start ---

Log-Message "Starting process to stop and clean up the distributed environment..."

# 1. Stop Middleware Nodes
if (Test-Path $PidFile) {
    Log-Message "Stopping middleware node processes..."
    $PIDs = Get-Content $PidFile
    foreach ($pid in $PIDs) {
        if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
            Log-Message "Stopping PID $pid..."
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500 # Small pause for process to terminate
        } else {
            Log-Message "PID $pid is no longer active."
        }
    }
    Remove-Item $PidFile
    Log-Message "Middleware node processes stopped."
} else {
    Log-Message "PID file '$PidFile' not found. No middleware nodes to stop via PID."
}

# 2. Stop Docker Databases
Log-Message "Stopping and removing MySQL containers with Docker Compose..."
if (-not (Check-Command "docker-compose")) {
    Log-Message "Error: 'docker-compose' not found. Please install Docker and Docker Compose."
    exit 1
}
Invoke-Expression "docker-compose down -v --remove-orphans" # '-v' removes volumes, ensures data is cleaned
if ($LASTEXITCODE -ne 0) {
    Log-Message "Error stopping Docker containers. Check Docker installation and 'docker-compose.yml'."
    exit 1
}
Log-Message "MySQL containers stopped and removed."

# 3. Clean up Logs
if (Test-Path $LogDir -PathType Container) {
    Log-Message "Removing logs directory '$LogDir'..."
    Remove-Item -Recurse -Force $LogDir
}

Log-Message "Distributed environment stopped and cleaned successfully!"
