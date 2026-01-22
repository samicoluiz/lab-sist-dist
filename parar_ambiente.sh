#!/bin/bash

# --- Variáveis de Configuração ---
PID_FILE="node_pids.tmp"
LOG_DIR="logs"

# --- Funções Auxiliares ---

log_message() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

# --- Início do Script ---

log_message "Iniciando processo de parada e limpeza do ambiente distribuído..."

# 1. Parar os nós do Middleware
if [ -f "$PID_FILE" ]; then
    log_message "Parando processos dos nós do middleware..."
    while IFS= read -r pid; do
        if kill -0 "$pid" >/dev/null 2>&1; then # Verifica se o processo ainda está ativo
            log_message "Encerrando PID $pid..."
            kill "$pid"
            sleep 0.5 # Pequena pausa para o processo encerrar
        else
            log_message "PID $pid não está mais ativo."
        fi
    done < "$PID_FILE"
    rm -f "$PID_FILE"
    log_message "Processos dos nós do middleware parados."
else
    log_message "Arquivo de PIDs '$PID_FILE' não encontrado. Nenhum nó do middleware para parar via PID."
fi

# 2. Parar os Bancos de Dados Docker
log_message "Parando e removendo contêineres MySQL com Docker Compose..."
if ! check_command "docker-compose"; then
    log_message "Erro: 'docker-compose' não encontrado. Por favor, instale o Docker e o Docker Compose."
    exit 1
fi
docker-compose down -v --remove-orphans # '-v' remove volumes, '-v' ensures data is cleaned
if [ $? -ne 0 ]; then
    log_message "Erro ao parar contêineres Docker. Verifique a instalação do Docker e o 'docker-compose.yml'."
    exit 1
fi
log_message "Contêineres MySQL parados e removidos."

# 3. Limpeza de Logs
if [ -d "$LOG_DIR" ]; then
    log_message "Removendo diretório de logs '$LOG_DIR'..."
    rm -rf "$LOG_DIR"
fi

# 4. Limpeza de config.json (opcional, pode ser útil manter)
# log_message "Removendo config.json..."
# rm -f config.json

log_message "Ambiente distribuído parado e limpo com sucesso!"
