#!/bin/bash

# --- Variáveis de Configuração ---
IPS_FILE="ips.txt"
PID_FILE="node_pids.tmp"
LOG_DIR="logs"
PYTHON_EXEC="python" # Use 'python3' se 'python' não funcionar

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
    timeout=60
    while ! nc -z "$host" "$port" >/dev/null 2>&1 && [ "$timeout" -gt 0 ]; do
        sleep 1
        timeout=$((timeout - 1))
    done
    if [ "$timeout" -eq 0 ]; then
        log_message "Erro: O banco de dados MySQL em $host:$port não está respondendo após 60 segundos."
        return 1
    fi
    log_message "Banco de dados MySQL em $host:$port está disponível."
    return 0
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
    # Ignorar linhas vazias e comentários
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    IPS+=("$line")
done < "$IPS_FILE"

if [ ${#IPS[@]} -eq 0 ]; then
    log_message "Erro: Nenhum endereço IP válido encontrado em '$IPS_FILE'."
    exit 1
fi

log_message "Endereços IP lidos do arquivo '$IPS_FILE': ${IPS[@]}"

# 2. Verificar e Instalar Dependências Python
log_message "Verificando dependências Python..."
if ! check_command "$PYTHON_EXEC"; then
    log_message "Erro: '$PYTHON_EXEC' não encontrado. Por favor, instale o Python ou ajuste a variável PYTHON_EXEC."
    exit 1
fi

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

# 3. Subir os Bancos de Dados Docker
log_message "Iniciando contêineres MySQL com Docker Compose..."
if ! check_command "docker-compose"; then
    log_message "Erro: 'docker-compose' não encontrado. Por favor, instale o Docker e o Docker Compose."
    exit 1
fi
docker-compose up -d
if [ $? -ne 0 ]; then
    log_message "Erro ao iniciar contêineres Docker. Verifique a instalação do Docker e o 'docker-compose.yml'."
    exit 1
fi
log_message "Contêineres MySQL iniciados."

# 4. Aguardar a prontidão dos Bancos de Dados
# Assume que o primeiro IP na lista e a porta 3306 serão suficientes para verificar a prontidão.
# Em um cenário real multi-máquina, seria necessário aguardar a porta 3306 de cada IP.
wait_for_db "${IPS[0]}" 3306
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
