# -*- coding: utf-8 -*-
# Script PowerShell para parada total e limpeza profunda

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Variáveis de Configuração ---
$PidFile = "node_pids.tmp"
$LogDir = "logs"

function Log-Message { Param ([string]$Message) Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message" }

Log-Message "Iniciando limpeza profunda do ambiente..."

# 1. Matar processos Python do Middleware
Log-Message "Encerrando todos os processos node.py..."
Get-CimInstance Win32_Process -Filter "Name LIKE 'python%.exe'" | Where-Object { $_.CommandLine -like "*node.py*" } | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}

# 2. Remover arquivos temporários
if (Test-Path $PidFile) { Remove-Item $PidFile -Force }

# 3. Docker Compose Down
Log-Message "Encerrando containers Docker..."
$DockerCmd = if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) { "docker-compose" } else { "docker compose" }
Invoke-Expression "$DockerCmd down -v --remove-orphans" | Out-Null

# 4. Limpar Logs (com retentativa caso estejam presos)
if (Test-Path $LogDir) {
    Log-Message "Limpando diretório de logs..."
    Start-Sleep -Seconds 1
    Remove-Item -Recurse -Force $LogDir -ErrorAction SilentlyContinue
}

Log-Message "Ambiente completamente limpo!"
