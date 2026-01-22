# -*- coding: utf-8 -*-
# Script PowerShell para iniciar o ambiente distribuído

# Configurar o console para usar UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- Variáveis de Configuração ---
$IpsFile = "ips.txt"
$PidFile = "node_pids.tmp"
$LogDir = "logs"
$PythonExec = "python" # Use 'python.exe' ou 'py -3' se 'python' não funcionar

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

function Wait-ForDb {
    Param (
        [string]$DbHost,
        [int]$Port
    )
    Log-Message "Aguardando o banco de dados MySQL em ${DbHost}:${Port} ficar disponível..."
    $timeout = 60
    while ($timeout -gt 0) {
        try {
            $socket = New-Object System.Net.Sockets.TcpClient($DbHost, $Port)
            if ($socket.Connected) {
                $socket.Close()
                Log-Message "Porta ${Port} aberta. Aguardando 20 segundos para inicialização completa do MySQL..."
                Start-Sleep -Seconds 20
                Log-Message "O banco de dados MySQL em ${DbHost}:${Port} deve estar pronto."
                return $true
            }
        } catch {
            # Falha na conexão, continuar aguardando
        }
        Start-Sleep -Seconds 1
        $timeout--
    }
    Log-Message "Erro: O banco de dados MySQL em ${DbHost}:${Port} não respondeu após 60 segundos."
    return $false
}

# --- Início do Script ---

Log-Message "Iniciando o processo de implantação do ambiente distribuído..."

# 0. Limpeza Prévia (Garantir que não há processos fantasmas)
Log-Message "Executando limpeza prévia do ambiente..."
& ".\parar_ambiente.ps1" | Out-Null

# 1. Ler IPs
if (-not (Test-Path $IpsFile)) {
    Log-Message "Erro: Arquivo '$IpsFile' não encontrado. Por favor, crie-o com um IP por linha."
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
    Log-Message "Erro: Nenhum endereço IP válido encontrado em '$IpsFile'."
    exit 1
}

Log-Message "Endereços IP lidos do arquivo '$IpsFile': $($IPs -join ', ')"

# 2. Verificar e Instalar Dependências Python
Log-Message "Verificando dependências Python..."
if (-not (Check-Command $PythonExec)) {
    Log-Message "Erro: '$PythonExec' não encontrado. Por favor, instale o Python ou ajuste a variável `$PythonExec`."
    exit 1
}

if (Test-Path "requirements.txt") {
    Invoke-Expression "$PythonExec -m pip install -r requirements.txt"
    if ($LASTEXITCODE -ne 0) {
        Log-Message "Erro ao instalar dependências Python. Verifique o 'requirements.txt' e sua conexão."
        exit 1
    }
    Log-Message "Dependências Python verificadas/instaladas."
} else {
    Log-Message "Aviso: 'requirements.txt' não encontrado. Pulando a instalação de dependências Python."
}

# 3. Subir os Bancos de Dados Docker
Log-Message "Iniciando contêineres MySQL com o Docker Compose..."

$FinalDockerCmd = ""
if (Check-Command "docker-compose") {
    $FinalDockerCmd = "docker-compose"
} elseif (docker compose version 2>&1 | Out-String -Stream | Select-String "version") {
    $FinalDockerCmd = "docker compose"
}

if ([string]::IsNullOrEmpty($FinalDockerCmd)) {
    Log-Message "Erro: 'docker-compose' ou plugin 'docker compose' não encontrado."
    exit 1
}

Log-Message "Usando comando: $FinalDockerCmd"
Invoke-Expression "$FinalDockerCmd up -d"
if ($LASTEXITCODE -ne 0) {
    Log-Message "Erro ao iniciar contêineres Docker."
    exit 1
}
Log-Message "Contêineres MySQL iniciados."

# 4. Aguardar a prontidão dos Bancos de Dados
if (-not (Wait-ForDb $IPs[0] 3309)) {
    Log-Message "Falha na inicialização do ambiente."
    exit 1
}

# 5. Gerar o arquivo config.json
Log-Message "Gerando config.json com base nos IPs fornecidos..."
$ConfigArgs = $IPs | ForEach-Object { "$_" }
Invoke-Expression "$PythonExec configurar.py $ConfigArgs"
if ($LASTEXITCODE -ne 0) {
    Log-Message "Erro ao gerar 'config.json'. Verifique 'configurar.py'."
    exit 1
}
Log-Message "Arquivo config.json gerado com sucesso."

# 6. Inicializar as Tabelas dos Bancos de Dados
Log-Message "Inicializando o esquema do banco de dados..."
Invoke-Expression "$PythonExec init_db.py"
if ($LASTEXITCODE -ne 0) {
    Log-Message "Erro ao inicializar os bancos de dados. Verifique 'init_db.py'."
    exit 1
}
Log-Message "Esquema do banco de dados inicializado."

# 7. Lançar os Nós do Middleware em segundo plano
Log-Message "Iniciando os nós do middleware em segundo plano..."
Remove-Item $PidFile -ErrorAction SilentlyContinue # Limpar arquivo de PID anterior
if (-not (Test-Path $LogDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null # Criar diretório de logs se não existir
}

for ($i = 0; $i -lt $IPs.Count; $i++) {
    Log-Message "Iniciando o nó $i..."
    # node.py agora lida com seu próprio log.
    $Process = Start-Process -FilePath $PythonExec -ArgumentList "node.py $i" -NoNewWindow -PassThru
    $Process.Id | Out-File -Append -FilePath $PidFile
    Log-Message "Nó $i iniciado com o PID $($Process.Id). Os logs estão em $LogDir\node$i.log"
}

Log-Message "Todos os nós do middleware foram iniciados em segundo plano."
Log-Message "Para interagir com o ambiente, use 'python client.py'."
Log-Message "Para parar o ambiente, execute '.\parar_ambiente.ps1'."
Log-Message "Implantação do ambiente concluída com sucesso!"
