import socket
import json

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5.0)
        print("Conectando a 127.0.0.1:5001...")
        s.connect(("127.0.0.1", 5001))
        print("Conectado!")
        msg = {"type": "CLIENT_QUERY", "sql": "SELECT 1 as test"}
        print(f"Enviando: {msg}")
        s.sendall(json.dumps(msg).encode())
        print("Aguardando resposta...")
        dados = s.recv(16384)
        if dados:
            print("Resposta recebida:", json.loads(dados.decode()))
        else:
            print("Nenhum dado recebido")
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")
