#!/bin/bash
# Script para rodar o cliente localmente (dentro do WSL)
# Usa config.local.json para evitar problemas de hairpin NAT

cd "$(dirname "$0")"

# Verifica se config.local.json existe
if [ ! -f "config.local.json" ]; then
    echo "Arquivo config.local.json não encontrado!"
    echo "Criando config.local.json..."
    cat > config.local.json << 'EOF'
{
  "nodes": [
    {
      "id": 0,
      "ip": "127.0.0.1",
      "port": 5000,
      "db_port": 3309
    },
    {
      "id": 1,
      "ip": "127.0.0.1",
      "port": 5001,
      "db_port": 3307
    },
    {
      "id": 2,
      "ip": "127.0.0.1",
      "port": 5002,
      "db_port": 3308
    }
  ]
}
EOF
fi

# Usa o Python do ambiente virtual se existir
if [ -d ".venv" ]; then
    .venv/bin/python client.py config.local.json
else
    python3 client.py config.local.json
fi
