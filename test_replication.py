import socket
import json

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

# Inserir dados no Nó 1
print("=== Inserindo dados no Nó 1 ===")
result = enviar_query("127.0.0.1", 5001, "INSERT INTO users (name, email) VALUES ('Teste Sync', 'sync@test.com')")
print(f"Resultado: {result}")

print("\n=== Aguardando 2 segundos para replicação ===")
import time
time.sleep(2)

# Verificar no Nó 0
print("\n=== Consultando Nó 0 (192.168.15.4:5000) ===")
result = enviar_query("192.168.15.4", 5000, "SELECT * FROM users WHERE email = 'sync@test.com'")
print(f"Resultado Nó 0: {result}")

# Verificar no Nó 1
print("\n=== Consultando Nó 1 (127.0.0.1:5001) ===")
result = enviar_query("127.0.0.1", 5001, "SELECT * FROM users WHERE email = 'sync@test.com'")
print(f"Resultado Nó 1: {result}")

# Verificar no Nó 2
print("\n=== Consultando Nó 2 (192.168.15.20:5002) ===")
result = enviar_query("192.168.15.20", 5002, "SELECT * FROM users WHERE email = 'sync@test.com'")
print(f"Resultado Nó 2: {result}")
