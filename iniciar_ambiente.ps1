# -*- coding: utf-8 -*-
# PowerShell script to start the distributed environment

# --- Configuration Variables ---
$IpsFile = "ips.txt"
$PidFile = "node_pids.tmp"
$LogDir = "logs"
$PythonExec = "python" # Use 'python.exe' or 'py -3' if 'python' does not work

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

function Wait-ForDb {
    Param (
        [string]$Host,
        [int]$Port
    )
    Log-Message "Waiting for MySQL database at ${Host}:${Port} to become available..."
    $timeout = 60
    while ($timeout -gt 0) {
        try {
            $socket = New-Object System.Net.Sockets.TcpClient($Host, $Port)
            if ($socket.Connected) {
                $socket.Close()
                Log-Message "MySQL database at ${Host}:${Port} is available."
                return $true
            }
        } catch {
            # Connection failed, continue waiting
        }
        Start-Sleep -Seconds 1
        $timeout--
    }
    Log-Message "Error: MySQL database at ${Host}:${Port} did not respond after 60 seconds."
    return $false
}

# --- Script Start ---

Log-Message "Starting distributed environment deployment process..."

# 1. Read IPs
if (-not (Test-Path $IpsFile)) {
    Log-Message "Error: File '$IpsFile' not found. Please create it with one IP per line."
    exit 1
}
$IPs = @()
(Get-Content $IpsFile) | ForEach-Object {
    $line = $_.Trim()
    if (-not [string]::IsNullOrEmpty($line) -and -not $line.StartsWith("#")) {
        $IPs += $line
    }
}

if ($IPs.Count -eq 0) {
    Log-Message "Error: No valid IP addresses found in '$IpsFile'."
    exit 1
}

Log-Message "IP addresses read from file '$IpsFile': $($IPs -join ', ')"

# 2. Check and Install Python Dependencies
Log-Message "Checking Python dependencies..."
if (-not (Check-Command $PythonExec)) {
    Log-Message "Error: '$PythonExec' not found. Please install Python or adjust the \$PythonExec variable."
    exit 1
}

if (Test-Path "requirements.txt") {
    Invoke-Expression "$PythonExec -m pip install -r requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Log-Message "Error installing Python dependencies. Check 'requirements.txt' and your connection."
        exit 1
    }
    Log-Message "Python dependencies checked/installed."
} else {
    Log-Message "Warning: 'requirements.txt' not found. Skipping Python dependency installation."
}

# 3. Bring up Docker Databases
Log-Message "Starting MySQL containers with Docker Compose..."
if (-not (Check-Command "docker-compose")) {
    Log-Message "Error: 'docker-compose' not found. Please install Docker and Docker Compose."
    exit 1
}
Invoke-Expression "docker-compose up -d"
if ($LASTEXITCODE -ne 0) {
    Log-Message "Error starting Docker containers. Check Docker installation and 'docker-compose.yml'."
    exit 1
}
Log-Message "MySQL containers started."

# 4. Wait for Databases to be ready
if (-not (Wait-ForDb $IPs[0] 3306)) {
    Log-Message "Environment initialization failed."
    exit 1
}

# 5. Generate config.json file
Log-Message "Generating config.json based on provided IPs..."
$ConfigArgs = $IPs | ForEach-Object { "$_" }
Invoke-Expression "$PythonExec configurar.py $ConfigArgs"
if ($LASTEXITCODE -ne 0) {
    Log-Message "Error generating 'config.json'. Check 'configurar.py'."
    exit 1
}
Log-Message "config.json file generated successfully."

# 6. Initialize Database Tables
Log-Message "Initializing database schema..."
Invoke-Expression "$PythonExec init_db.py"
if ($LASTEXITCODE -ne 0) {
    Log-Message "Error initializing databases. Check 'init_db.py'."
    exit 1
}
Log-Message "Database schema initialized."

# 7. Launch Middleware Nodes in background
Log-Message "Starting middleware nodes in background..."
Remove-Item $PidFile -ErrorAction SilentlyContinue # Clear previous PID file
if (-not (Test-Path $LogDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null # Create logs directory if it doesn't exist
}

for ($i = 0; $i -lt $IPs.Count; $i++) {
    Log-Message "Starting node $i..."
    # node.py now handles its own logging.
    $Process = Start-Process -FilePath $PythonExec -ArgumentList "node.py $i" -NoNewWindow -PassThru
    $Process.Id | Out-File -Append -FilePath $PidFile
    Log-Message "Node $i started with PID $($Process.Id). Logs are in $LogDir\node$i.log"
}

Log-Message "All middleware nodes have been started in the background."
Log-Message "To interact with the environment, use 'python client.py'."
Log-Message "To stop the environment, execute '.\parar_ambiente.ps1'."
Log-Message "Environment deployment completed successfully!"
