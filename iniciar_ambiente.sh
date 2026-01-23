#!/bin/bash

# --- Variáveis de Configuração ---
IPS_FILE="ips.txt"
PID_FILE="node_pids.tmp"
LOG_DIR="logs"
PYTHON_EXEC="python3" # Use 'python' se 'python3' não funcionar

# --- Funções Auxiliares ---

log_message() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

wait_for_db() {
    local host=$1
    local port=$2
    log_message "Aguardando o banco de dados MySQL em $host:$port ficar disponível..."
    log_message "DEBUG: Testando comando nc..."
    which nc
    nc -z "$host" "$port" && log_message "DEBUG: nc test succeeded" || log_message "DEBUG: nc test failed"
    local wait_timeout=120
    local count=0
    while [ "$count" -lt "$wait_timeout" ]; do
        if nc -z "$host" "$port" >/dev/null 2>&1; then
            log_message "Banco de dados MySQL em $host:$port está disponível."
            return 0
        fi
        sleep 1
        count=$((count + 1))
        if [ $((count % 10)) -eq 0 ]; then
            log_message "Ainda aguardando... ($count segundos)"
        fi
    done
    log_message "Erro: O banco de dados MySQL em $host:$port não está respondendo após $wait_timeout segundos."
    return 1
}

# --- Início do Script ---

log_message "Iniciando processo de implantação do ambiente distribuído..."

# 1. Verificar IPs
if [ ! -f "$IPS_FILE" ]; then
    log_message "Erro: Arquivo '$IPS_FILE' não encontrado. Crie-o com um IP por linha."
    exit 1
fi
IPS=()
while IFS= read -r line; do
    # Remover carriage return (Windows line ending)
    line="${line%$'\r'}"
    # Ignorar linhas vazias e comentários
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IPS+=("$line")
done < "$IPS_FILE"

if [ ${#IPS[@]} -eq 0 ]; then
    log_message "Erro: Nenhum endereço IP válido encontrado em '$IPS_FILE'."
    exit 1
fi

log_message "Endereços IP lidos do arquivo '$IPS_FILE': ${IPS[@]}"

# 2. Configurar Ambiente Virtual (Venv) para evitar erro PEP 668
log_message "Configurando ambiente virtual Python..."
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    log_message "Criando ambiente virtual em '$VENV_DIR'..."
    "$PYTHON_EXEC" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        log_message "Erro: Falha ao criar ambiente virtual. Pode ser necessário instalar o pacote 'python3-venv'."
        log_message "Tente executar: sudo apt update && sudo apt install python3-venv"
        exit 1
    fi
fi

# Atualizar PYTHON_EXEC para usar o python do ambiente virtual
PYTHON_EXEC="$VENV_DIR/bin/python"
log_message "Usando Python do ambiente virtual: $PYTHON_EXEC"

# Verificar se o pip está instalado no venv
"$PYTHON_EXEC" -m pip --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    log_message "Aviso: Pip não encontrado no ambiente virtual. Tentando instalar via ensurepip..."
    "$PYTHON_EXEC" -m ensurepip --upgrade --default-pip
    if [ $? -ne 0 ]; then
        log_message "Erro: Falha ao instalar o pip via ensurepip."
        log_message "Isso indica uma instalação incompleta do Python."
        log_message "POR FAVOR, REALIZE A CORREÇÃO ABAIXO DE ACORDO COM SEU SISTEMA:"
        log_message "  1. Remova o venv quebrado:  rm -rf .venv"
        log_message "  2. Instale os pacotes necessários:"
        log_message "     [Debian/Ubuntu/WSL]: sudo apt update && sudo apt install python3-venv python3-pip"
        log_message "     [Arch Linux]:        sudo pacman -S python (O Arch geralmente já inclui tudo, mas reinstalar pode corrigir)"
        log_message "     [Fedora]:            sudo dnf install python3-pip"
        log_message "  3. Tente rodar o script novamente."
        exit 1
    fi
    log_message "Pip instalado com sucesso no ambiente virtual."
fi

# 3. Verificar e Instalar Dependências Python
log_message "Instalando dependências no ambiente virtual..."
if [ -f "requirements.txt" ]; then
    "$PYTHON_EXEC" -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        log_message "Erro ao instalar dependências Python. Verifique o 'requirements.txt' e sua conexão."
        exit 1
    fi
    log_message "Dependências Python verificadas/instaladas."
else
    log_message "Aviso: 'requirements.txt' não encontrado. Pulando instalação de dependências Python."
fi

# 4. Subir os Bancos de Dados Docker
log_message "Verificando Docker Compose..."
DOCKER_COMPOSE_CMD=""

if check_command "docker-compose"; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

if [ -z "$DOCKER_COMPOSE_CMD" ]; then
    log_message "Erro: 'docker-compose' ou plugin 'docker compose' não encontrado."
    log_message "Por favor, instale o Docker e o Docker Compose."
    exit 1
fi

log_message "Usando comando Docker: '$DOCKER_COMPOSE_CMD'"
log_message "Iniciando contêineres MySQL..."

$DOCKER_COMPOSE_CMD up -d
if [ $? -ne 0 ]; then
    log_message "Erro ao iniciar contêineres Docker. Verifique a instalação do Docker e o 'docker-compose.yml'."
    exit 1
fi
log_message "Contêineres MySQL iniciados."

# 4. Aguardar a prontidão dos Bancos de Dados
# Assume que o primeiro IP na lista e a porta 3309 serão suficientes para verificar a prontidão.
# Em um cenário real multi-máquina, seria necessário aguardar a porta correspondente de cada IP.
wait_for_db "${IPS[0]}" 3309
if [ $? -ne 0 ]; then
    log_message "Falha na inicialização do ambiente."
    exit 1
fi

# 5. Gerar o arquivo config.json
log_message "Gerando arquivo config.json com base nos IPs fornecidos..."
"$PYTHON_EXEC" configurar.py "${IPS[@]}"
if [ $? -ne 0 ]; then
    log_message "Erro ao gerar 'config.json'. Verifique 'configurar.py'."
    exit 1
fi
log_message "Arquivo config.json gerado com sucesso."

# 6. Inicializar as Tabelas dos Bancos de Dados
log_message "Inicializando esquema dos bancos de dados..."
"$PYTHON_EXEC" init_db.py
if [ $? -ne 0 ]; then
    log_message "Erro ao inicializar bancos de dados. Verifique 'init_db.py'."
    exit 1
fi
log_message "Esquema dos bancos de dados inicializado."

# 7. Lançar os Nós do Middleware em segundo plano
log_message "Iniciando nós do middleware em segundo plano..."
rm -f "$PID_FILE" # Limpa o arquivo de PIDs anterior
mkdir -p "$LOG_DIR" # Cria diretório de logs se não existir

for i in "${!IPS[@]}"; do
    log_message "Iniciando nó $i..."
    # Redireciona a saída para um arquivo de log e executa em background
    "$PYTHON_EXEC" node.py "$i" > "$LOG_DIR/node$i.log" 2>&1 &
    PID=$!
    echo "$PID" >> "$PID_FILE"
    log_message "Nó $i iniciado com PID $PID. Logs em $LOG_DIR/node$i.log"
done

log_message "Todos os nós do middleware foram iniciados em segundo plano."
log_message "Para interagir com o ambiente, use 'python client.py'."
log_message "Para parar o ambiente, execute './parar_ambiente.sh'."
log_message "Implantação do ambiente concluída com sucesso!"
