#!/usr/bin/env python3
"""
TESTE SIMPLES DE CONECTIVIDADE
Execute na outra máquina (Windows, Linux, qualquer SO com Python)
"""
import socket
import sys

IP_ALVO = "192.168.15.6"
PORTAS = [3307, 5001, 5002]

print("=" * 60)
print(f"TESTE DE CONECTIVIDADE: {IP_ALVO}")
print("=" * 60)
print()

resultados = []

for porta in PORTAS:
    print(f"Testando {IP_ALVO}:{porta}...", end=" ")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        resultado = sock.connect_ex((IP_ALVO, porta))
        sock.close()
        
        if resultado == 0:
            print("✓ ACESSÍVEL")
            resultados.append(True)
        else:
            print("✗ BLOQUEADA")
            resultados.append(False)
    except Exception as e:
        print(f"✗ ERRO: {e}")
        resultados.append(False)

print()
print("=" * 60)
if all(resultados):
    print("✓ SUCESSO! Todas as portas estão acessíveis!")
    print("  O port forwarding está funcionando corretamente")
elif any(resultados):
    print("⚠ PARCIAL: Algumas portas acessíveis, outras bloqueadas")
    print("  Verifique as regras de port forwarding")
else:
    print("✗ FALHA TOTAL: Nenhuma porta acessível")
    print()
    print("POSSÍVEIS CAUSAS:")
    print("  1. Firewall do roteador bloqueando")
    print("  2. AP Isolation ativado no WiFi")
    print("  3. Máquinas em VLANs diferentes")
    print("  4. Port forwarding não configurado no Windows")
    print()
    print("TESTE BÁSICO:")
    print("  Execute na outra máquina:")
    print("    ping 192.168.15.6")
    print("  Se o ping falhar, o problema é de rede (roteador)")
print("=" * 60)
