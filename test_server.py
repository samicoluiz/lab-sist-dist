import socket
import json
import threading

def tratar_cliente(conn, addr):
    print(f"Thread started for {addr}", flush=True)
    try:
        print(f"Receiving data from {addr}...", flush=True)
        dados = conn.recv(8192)
        print(f"Received {len(dados) if dados else 0} bytes from {addr}", flush=True)
        if not dados:
            print(f"No data from {addr}", flush=True)
            conn.close()
            return
        msg = json.loads(dados.decode())
        print(f"Parsed message: {msg}", flush=True)
        
        # Echo back
        response = {"status": "success", "echo": msg}
        print(f"Sending response to {addr}...", flush=True)
        conn.sendall(json.dumps(response).encode())
        print(f"Response sent to {addr}", flush=True)
    except Exception as e:
        print(f"Error handling {addr}: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()
    finally:
        print(f"Closing connection from {addr}", flush=True)
        conn.close()

print("Starting test server on 5001...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('0.0.0.0', 5001))
sock.listen(10)
print("Server listening on port 5001")

try:
    while True:
        conn, addr = sock.accept()
        print(f"Accepted connection from {addr}", flush=True)
        threading.Thread(target=tratar_cliente, args=(conn, addr), daemon=False).start()
except KeyboardInterrupt:
    print("Server stopped")
