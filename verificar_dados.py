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

# Consultar todos os usuários em cada nó
print("=== TODOS OS USUÁRIOS EM CADA NÓ ===\n")

print("Nó 0 (192.168.15.4:5000):")
result = enviar_query("192.168.15.4", 5000, "SELECT * FROM users ORDER BY email")
if result.get('status') == 'success':
    for user in result.get('data', []):
        print(f"  - ID {user['id']}: {user['name']} ({user['email']})")
    print(f"  Total: {len(result.get('data', []))} usuários")
else:
    print(f"  Erro: {result}")

print("\nNó 1 (127.0.0.1:5001):")
result = enviar_query("127.0.0.1", 5001, "SELECT * FROM users ORDER BY email")
if result.get('status') == 'success':
    for user in result.get('data', []):
        print(f"  - ID {user['id']}: {user['name']} ({user['email']})")
    print(f"  Total: {len(result.get('data', []))} usuários")
else:
    print(f"  Erro: {result}")

print("\nNó 2 (192.168.15.20:5002):")
result = enviar_query("192.168.15.20", 5002, "SELECT * FROM users ORDER BY email")
if result.get('status') == 'success':
    for user in result.get('data', []):
        print(f"  - ID {user['id']}: {user['name']} ({user['email']})")
    print(f"  Total: {len(result.get('data', []))} usuários")
else:
    print(f"  Erro: {result}")
