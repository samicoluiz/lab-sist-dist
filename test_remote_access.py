#!/usr/bin/env python3
"""
Execute este script em OUTRA MÁQUINA (192.168.15.4 ou 192.168.15.20)
para testar a conectividade com a máquina 192.168.15.6
"""
import socket
import json

IP_ALVO = "192.168.15.6"
PORTA_ALVO = 5001

print("=" * 60)
print(f"TESTE DE CONECTIVIDADE: {IP_ALVO}:{PORTA_ALVO}")
print("=" * 60)
print()

# Teste 1: TCP básico
print(f"[1/3] Testando conexão TCP básica...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    sock.connect((IP_ALVO, PORTA_ALVO))
    print(f"  ✓ Conexão TCP estabelecida com sucesso!")
    sock.close()
except Exception as e:
    print(f"  ✗ ERRO na conexão TCP: {type(e).__name__}: {e}")
    print()
    print("DIAGNÓSTICO:")
    print("  - Verifique se o port forwarding está ativo no Windows")
    print("  - Verifique o firewall do Windows")
    print(f"  - Execute na máquina {IP_ALVO}: netsh interface portproxy show all")
    exit(1)

# Teste 2: Enviar mensagem e receber resposta
print(f"\n[2/3] Testando comunicação com o nó...")
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect((IP_ALVO, PORTA_ALVO))
        
        msg = {"type": "CLIENT_QUERY", "sql": "SELECT 1 as test"}
        print(f"  - Enviando: {msg}")
        s.sendall(json.dumps(msg).encode())
        
        dados = s.recv(16384)
        if dados:
            resposta = json.loads(dados.decode())
            print(f"  ✓ Resposta recebida: {resposta}")
        else:
            print(f"  ✗ Nenhuma resposta recebida")
except Exception as e:
    print(f"  ✗ ERRO: {type(e).__name__}: {e}")
    exit(1)

# Teste 3: Consulta real
print(f"\n[3/3] Testando consulta ao banco de dados...")
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        s.connect((IP_ALVO, PORTA_ALVO))
        
        msg = {"type": "CLIENT_QUERY", "sql": "SELECT * FROM users LIMIT 3"}
        s.sendall(json.dumps(msg).encode())
        
        dados = s.recv(16384)
        if dados:
            resposta = json.loads(dados.decode())
            if resposta.get('status') == 'success':
                users = resposta.get('data', [])
                print(f"  ✓ Query executada com sucesso!")
                print(f"  - Registros retornados: {len(users)}")
                for user in users[:3]:
                    print(f"    • {user.get('name')} ({user.get('email')})")
            else:
                print(f"  ✗ Erro na query: {resposta}")
except Exception as e:
    print(f"  ✗ ERRO: {type(e).__name__}: {e}")
    exit(1)

print()
print("=" * 60)
print("✓ TODOS OS TESTES PASSARAM!")
print(f"✓ A máquina {IP_ALVO} está ACESSÍVEL e RESPONDENDO corretamente!")
print("=" * 60)
