#!/usr/bin/env python3
"""
Script para sincronizar dados entre todos os nós do sistema distribuído.
ATENÇÃO: Isso vai DELETAR todos os dados e recriar a partir do nó fonte.
"""
import socket
import json
import sys

def enviar_query(ip, porta, sql):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((ip, porta))
            msg = {"type": "CLIENT_QUERY", "sql": sql}
            s.sendall(json.dumps(msg).encode())
            dados = s.recv(16384)
            if dados:
                return json.loads(dados.decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Carregar configuração
with open('config.json', 'r') as f:
    config = json.load(f)
    nodes = config['nodes']

print("=" * 60)
print("SINCRONIZAÇÃO DE DADOS ENTRE NÓS")
print("=" * 60)
print()
print("ATENÇÃO: Este script irá:")
print("1. Ler todos os dados de UM nó (fonte)")
print("2. DELETAR todos os dados dos outros nós")
print("3. Inserir os dados do nó fonte nos outros nós")
print()

# Mostrar nós disponíveis
print("Nós disponíveis:")
for node in nodes:
    print(f"  {node['id']}: {node['ip']}:{node['port']}")

# Escolher nó fonte
print()
fonte_id = int(input("Digite o ID do nó FONTE (de onde copiar os dados): "))
node_fonte = next((n for n in nodes if n['id'] == fonte_id), None)

if not node_fonte:
    print("Nó não encontrado!")
    sys.exit(1)

print(f"\nNó fonte: Nó {node_fonte['id']} ({node_fonte['ip']}:{node_fonte['port']})")
confirma = input("\nConfirma sincronização? Todos os outros nós serão SOBRESCRITOS! (sim/não): ")

if confirma.lower() != 'sim':
    print("Cancelado.")
    sys.exit(0)

# Ler dados do nó fonte
print(f"\n[1/3] Lendo dados do Nó {node_fonte['id']}...")
result = enviar_query(node_fonte['ip'], node_fonte['port'], "SELECT * FROM users")

if result.get('status') != 'success':
    print(f"Erro ao ler dados: {result}")
    sys.exit(1)

users = result.get('data', [])
print(f"  ✓ {len(users)} usuários encontrados")

# Sincronizar com outros nós
outros_nos = [n for n in nodes if n['id'] != fonte_id]

for node in outros_nos:
    print(f"\n[2/3] Sincronizando Nó {node['id']} ({node['ip']}:{node['port']})...")
    
    # Limpar dados existentes
    print(f"  - Limpando dados...")
    result = enviar_query(node['ip'], node['port'], "DELETE FROM users")
    if result.get('status') != 'success':
        print(f"  ✗ Erro ao limpar: {result}")
        continue
    
    # Inserir dados
    print(f"  - Inserindo {len(users)} usuários...")
    for user in users:
        sql = f"INSERT INTO users (name, email) VALUES ('{user['name']}', '{user['email']}')"
        result = enviar_query(node['ip'], node['port'], sql)
        if result.get('status') != 'success':
            print(f"  ✗ Erro ao inserir {user['name']}: {result}")
    
    print(f"  ✓ Nó {node['id']} sincronizado")

print("\n[3/3] Verificando sincronização...")
for node in nodes:
    result = enviar_query(node['ip'], node['port'], "SELECT COUNT(*) as total FROM users")
    if result.get('status') == 'success':
        total = result['data'][0]['total']
        print(f"  Nó {node['id']}: {total} usuários")

print("\n" + "=" * 60)
print("SINCRONIZAÇÃO CONCLUÍDA!")
print("=" * 60)
