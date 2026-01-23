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

# 7. Detectar IP local e iniciar apenas o nó correspondente
Log-Message "Detectando IP local da máquina..."

# Ler IP do arquivo .env se existir
$MY_IP = $null
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^MY_IP=(.+)$') {
            $MY_IP = $Matches[1].Trim()
            Log-Message "IP lido do arquivo .env: $MY_IP"
        }
    }
}

# Se MY_IP ainda está vazio, tentar detectar automaticamente
if ([string]::IsNullOrEmpty($MY_IP)) {
    Log-Message "Tentando detectar IP automaticamente..."
    $MY_IP = (Get-NetIPAddress -AddressFamily IPv4 | 
              Where-Object {$_.InterfaceAlias -notlike '*Loopback*' -and 
                           $_.InterfaceAlias -notlike '*WSL*' -and 
                           $_.IPAddress -like '192.168.*'}).IPAddress | 
              Select-Object -First 1
}

Log-Message "IP local detectado: $MY_IP"

# Encontrar qual nó deve rodar nesta máquina
$MY_NODE_ID = -1
for ($i = 0; $i -lt $IPs.Count; $i++) {
    if ($IPs[$i].Trim() -eq $MY_IP) {
        $MY_NODE_ID = $i
        break
    }
}

Remove-Item $PidFile -ErrorAction SilentlyContinue
if (-not (Test-Path $LogDir -PathType Container)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

if ($MY_NODE_ID -eq -1) {
    Log-Message "AVISO: IP local ($MY_IP) não encontrado em ips.txt"
    Log-Message "IPs no arquivo: $($IPs -join ', ')"
    Log-Message "Iniciando todos os nós localmente para teste..."
    
    # Modo de teste local - iniciar todos os nós
    $ConfigFile = "config.local.json"
    
    # Criar config.local.json se não existir
    if (-not (Test-Path $ConfigFile)) {
        $localConfig = @{
            nodes = @(
                @{id=0; ip="127.0.0.1"; port=5000; db_port=3309},
                @{id=1; ip="127.0.0.1"; port=5001; db_port=3307},
                @{id=2; ip="127.0.0.1"; port=5002; db_port=3308}
            )
        }
        $localConfig | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile
    }
    
    for ($i = 0; $i -lt $IPs.Count; $i++) {
        Log-Message "Iniciando nó $i com $ConfigFile (modo teste)..."
        $Process = Start-Process -FilePath $PythonExec -ArgumentList "node.py $i $ConfigFile" -NoNewWindow -PassThru
        $Process.Id | Out-File -Append -FilePath $PidFile
        Log-Message "Nó $i iniciado com PID $($Process.Id). Logs em $LogDir\node$i.log"
    }
} else {
    # Modo distribuído - iniciar apenas o nó desta máquina
    Log-Message "Iniciando apenas o nó $MY_NODE_ID (correspondente a $MY_IP)..."
    $ConfigFile = "config.json"
    
    $Process = Start-Process -FilePath $PythonExec -ArgumentList "node.py $MY_NODE_ID $ConfigFile" -NoNewWindow -PassThru
    $Process.Id | Out-File -Append -FilePath $PidFile
    Log-Message "Nó $MY_NODE_ID iniciado com PID $($Process.Id). Logs em $LogDir\node$MY_NODE_ID.log"
}

Log-Message "Nós do middleware iniciados em segundo plano."
Log-Message "Para interagir com o ambiente, use 'python client.py'."
Log-Message "Para parar o ambiente, execute '.\parar_ambiente.ps1'."
Log-Message "Implantação do ambiente concluída com sucesso!"
