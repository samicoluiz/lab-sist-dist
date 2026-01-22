# -*- coding: utf-8 -*-
# Script PowerShell para parar e limpar o ambiente distribuído

# --- Variáveis de Configuração ---
$PidFile = "node_pids.tmp"
$LogDir = "logs"

# --- Funções Auxiliares ---

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

# --- Início do Script ---

Log-Message "Iniciando o processo de parada e limpeza do ambiente distribuído..."

# 1. Parar os nós do Middleware
if (Test-Path $PidFile) {
    Log-Message "Parando os processos dos nós do middleware..."
    $PIDs = Get-Content $PidFile
    foreach ($pid in $PIDs) {
        if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
            Log-Message "Encerrando PID $pid..."
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500 # Pequena pausa para o processo encerrar
        } else {
            Log-Message "O PID $pid não está mais ativo."
        }
    }
    Remove-Item $PidFile
    Log-Message "Processos dos nós do middleware parados."
} else {
    Log-Message "Arquivo de PID '$PidFile' não encontrado. Nenhum nó do middleware para parar via PID."
}

# 2. Parar os Bancos de Dados Docker
Log-Message "Parando e removendo contêineres MySQL com o Docker Compose..."

DOCKER_COMPOSE_CMD=""
if (Check-Command "docker-compose") {
    $DOCKER_COMPOSE_CMD = "docker-compose"
} else {
    # Verificar se 'docker compose' (v2 plugin) está disponível
    # Em PowerShell, é um pouco diferente testar o comando com espaço
    if (& docker compose version 2>&1 | Out-String -Stream | Select-String "version") {
        $DOCKER_COMPOSE_CMD = "docker compose"
    }
}

if ([string]::IsNullOrEmpty($DOCKER_COMPOSE_CMD)) {
    Log-Message "Erro: 'docker-compose' ou plugin 'docker compose' não encontrado."
    exit 1
}

Invoke-Expression "$DOCKER_COMPOSE_CMD down -v --remove-orphans" # '-v' remove volumes, garante que os dados sejam limpos
if ($LASTEXITCODE -ne 0) {
    Log-Message "Erro ao parar os contêineres Docker. Verifique a instalação do Docker e o 'docker-compose.yml'."
    exit 1
}
Log-Message "Contêineres MySQL parados e removidos."

# 3. Limpeza de Logs
if (Test-Path $LogDir -PathType Container) {
    Log-Message "Removendo o diretório de logs '$LogDir'..."
    Remove-Item -Recurse -Force $LogDir
}

Log-Message "Ambiente distribuído parado e limpo com sucesso!"