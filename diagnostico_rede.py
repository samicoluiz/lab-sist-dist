#!/usr/bin/env python3
"""
Execute na OUTRA MÁQUINA para testar conectividade básica
"""
import subprocess
import socket

IP_ALVO = "192.168.15.6"

print("=" * 60)
print(f"DIAGNÓSTICO DE CONECTIVIDADE COM {IP_ALVO}")
print("=" * 60)
print()

# Teste 1: PING
print("[1/4] Testando PING...")
try:
    result = subprocess.run(['ping', '-c', '4', IP_ALVO], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print(f"  ✓ PING bem-sucedido!")
        print(f"    {[line for line in result.stdout.split('\\n') if 'time=' in line][0].strip()}")
    else:
        print(f"  ✗ PING falhou!")
        print(f"    Outras máquinas NÃO conseguem alcançar {IP_ALVO}")
        print(f"    CAUSA: Firewall de rede ou isolamento AP ativado")
        print()
        print("SOLUÇÃO:")
        print("  1. Verifique o roteador/WiFi")
        print("  2. Desabilite 'AP Isolation' ou 'Client Isolation'")
        print("  3. Verifique se as máquinas estão na mesma VLAN/subnet")
        exit(1)
except Exception as e:
    print(f"  ✗ ERRO ao executar ping: {e}")
    exit(1)

# Teste 2: Porta MySQL
print(f"\n[2/4] Testando porta MySQL (3307)...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    result = sock.connect_ex((IP_ALVO, 3307))
    sock.close()
    if result == 0:
        print(f"  ✓ Porta 3307 ACESSÍVEL")
    else:
        print(f"  ✗ Porta 3307 BLOQUEADA (firewall ou port forwarding)")
except Exception as e:
    print(f"  ✗ ERRO: {e}")

# Teste 3: Porta do nó
print(f"\n[3/4] Testando porta do nó (5001)...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3.0)
    result = sock.connect_ex((IP_ALVO, 5001))
    sock.close()
    if result == 0:
        print(f"  ✓ Porta 5001 ACESSÍVEL")
    else:
        print(f"  ✗ Porta 5001 BLOQUEADA")
        print(f"    Mas o PING funcionou, então o problema é:")
        print(f"    - Firewall do Windows (improvável, já testado)")
        print(f"    - Port forwarding não está funcionando")
        print(f"    - Antivírus bloqueando")
except Exception as e:
    print(f"  ✗ ERRO: {e}")

# Teste 4: Traceroute simplificado
print(f"\n[4/4] Testando rota até {IP_ALVO}...")
try:
    result = subprocess.run(['traceroute', '-m', '5', IP_ALVO], 
                          capture_output=True, text=True, timeout=15)
    print(result.stdout)
except:
    print("  (traceroute não disponível)")

print()
print("=" * 60)
