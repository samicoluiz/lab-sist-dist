import socket
import json

# Testa conectando pelo IP externo (192.168.15.6) ao invés de localhost
IP_TESTE = "192.168.15.6"
PORTA = 5001

print(f"Testando conexão EXTERNA via {IP_TESTE}:{PORTA}")
print("(simulando como se fosse de outra máquina)")
print()

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        print(f"[1] Conectando a {IP_TESTE}:{PORTA}...")
        s.connect((IP_TESTE, PORTA))
        print("  ✓ Conectado!")
        
        print(f"[2] Enviando query...")
        msg = {"type": "CLIENT_QUERY", "sql": "SELECT 1 as test"}
        s.sendall(json.dumps(msg).encode())
        
        print(f"[3] Aguardando resposta...")
        dados = s.recv(16384)
        if dados:
            resposta = json.loads(dados.decode())
            print(f"  ✓ Resposta: {resposta}")
            print()
            print("✓ SUCESSO! A porta está acessível via IP externo")
            print("  O problema pode estar no roteador ou firewall de rede")
        else:
            print("  ✗ Nenhuma resposta")
except socket.timeout:
    print()
    print("✗ TIMEOUT!")
    print()
    print("DIAGNÓSTICO:")
    print("  1. O port forwarding NÃO está funcionando corretamente")
    print("  2. Possíveis causas:")
    print("     - Antivírus bloqueando (Windows Defender, etc.)")
    print("     - Hyper-V Virtual Switch com problema")
    print("     - Serviço iphlpsvc precisa ser reiniciado")
    print()
    print("SOLUÇÕES:")
    print("  A) Desabilite temporariamente o antivírus")
    print("  B) Execute: Restart-Service iphlpsvc -Force")
    print("  C) Reinicie o Windows")
except Exception as e:
    print(f"✗ ERRO: {type(e).__name__}: {e}")
