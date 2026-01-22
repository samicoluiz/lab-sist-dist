import socket
import json
import sys
import random

def send_query(node_info, sql):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((node_info['ip'], node_info['port']))
            msg = {'type': 'CLIENT_QUERY', 'sql': sql}
            s.sendall(json.dumps(msg).encode())
            
            data = s.recv(16384)
            if data:
                return json.loads(data.decode())
    except Exception as e:
        return {"status": "error", "message": str(e)}

def find_coordinator(nodes):
    """Pergunta aos nós quem é o atual coordenador."""
    print("Procurando coordenador...")
    for node in nodes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((node['ip'], node['port']))
                msg = {'type': 'GET_COORDINATOR'}
                s.sendall(json.dumps(msg).encode())
                
                data = s.recv(1024)
                if data:
                    response = json.loads(data.decode())
                    if response.get('status') == 'success':
                        coord_id = response.get('coordinator_id')
                        if coord_id is not None:
                            return coord_id
        except:
            continue
    return None

def main():
    try:
        with open('config.json', 'r') as f:
            nodes = json.load(f)['nodes']
    except FileNotFoundError:
        print("config.json não encontrado.")
        return

    print("--- Cliente de Banco de Dados Distribuído ---")
    
    while True:
        print("\nNós Disponíveis:")
        for i, n in enumerate(nodes):
            print(f"{i}: Nó {n['id']} ({n['ip']}:{n['port']})")
        print("a: Auto (Balanceamento de Carga Aleatório)")
        print("c: Coordenador (Enviar para o Líder)")
        
        try:
            choice = input("\nSelecione o índice do nó, 'a' ou 'c' (ou 'q' para sair): ")
            if choice.lower() == 'q':
                break
            
            node_idx = -1
            
            if choice.lower() == 'a':
                node_idx = random.randint(0, len(nodes) - 1)
                print(f"Nó selecionado automaticamente: {nodes[node_idx]['id']}")
            elif choice.lower() == 'c':
                coord_id = find_coordinator(nodes)
                if coord_id is not None:
                    # Find index of coordinator
                    for i, n in enumerate(nodes):
                        if n['id'] == coord_id:
                            node_idx = i
                            break
                    print(f"Coordenador selecionado automaticamente: Nó {coord_id}")
                else:
                    print("Não foi possível encontrar um coordenador (ou o cluster está fora do ar).")
                    continue
            else:
                node_idx = int(choice)
                if node_idx < 0 or node_idx >= len(nodes):
                    print("Índice inválido.")
                    continue
                
            sql = input("Digite a query SQL: ")
            if not sql:
                continue
                
            result = send_query(nodes[node_idx], sql)
            
            print("\n--- Resultado ---")
            print(json.dumps(result, indent=2))
            print("--------------")
            
        except ValueError:
            print("Por favor, insira uma opção válida.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()