import socket
import json
import sys
import random

def _enviar_requisicao(ip, porta, mensagem, timeout=5.0):
    """
    Função auxiliar para enviar uma mensagem JSON para um nó e receber uma resposta JSON.
    Retorna None se a conexão falhar.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, porta))
            s.sendall(json.dumps(mensagem).encode())
            
            # Usando recv para garantir que recebemos alguns dados, 
            # embora para JSON curto, 16KB geralmente seja suficiente.
            dados = s.recv(16384)
            if dados:
                return json.loads(dados.decode())
    except Exception as e:
        # Para depuração, poderia imprimir 'e', mas para fluxo de cliente retornamos None/dict de erro
        pass
    return None

def enviar_query(info_no, sql):
    msg = {'type': 'CLIENT_QUERY', 'sql': sql}
    resposta = _enviar_requisicao(info_no['ip'], info_no['port'], msg)
    if resposta:
        return resposta
    return {"status": "error", "message": "Falha na conexão com o nó."}

def encontrar_coordenador(nos):
    """Pergunta aos nós quem é o atual coordenador."""
    print("Procurando coordenador...")
    for no in nos:
        msg = {'type': 'GET_COORDINATOR'}
        resposta = _enviar_requisicao(no['ip'], no['port'], msg, timeout=2.0)
        
        if resposta and resposta.get('status') == 'success':
            id_coord = resposta.get('coordinator_id')
            if id_coord is not None:
                return id_coord
    return None

def principal():
    try:
        with open('config.json', 'r') as f:
            nos = json.load(f)['nodes']
    except FileNotFoundError:
        print("config.json não encontrado.")
        return

    print("--- Cliente de Banco de Dados Distribuído ---")
    
    while True:
        print("\nNós Disponíveis:")
        for i, n in enumerate(nos):
            print(f"{i}: Nó {n['id']} ({n['ip']}:{n['port']})")
        print("a: Auto (Balanceamento de Carga Aleatório)")
        print("c: Coordenador (Enviar para o Líder)")
        
        try:
            escolha = input("\nSelecione o índice do nó, 'a' ou 'c' (ou 'q' para sair): ")
            if escolha.lower() == 'q':
                break
            
            indice_no = -1
            
            if escolha.lower() == 'a':
                indice_no = random.randint(0, len(nos) - 1)
                print(f"Nó selecionado automaticamente: {nos[indice_no]['id']}")
            elif escolha.lower() == 'c':
                id_coord = encontrar_coordenador(nos)
                if id_coord is not None:
                    # Encontrar índice do coordenador
                    for i, n in enumerate(nos):
                        if n['id'] == id_coord:
                            indice_no = i
                            break
                    print(f"Coordenador selecionado automaticamente: Nó {id_coord}")
                else:
                    print("Não foi possível encontrar um coordenador (ou o cluster está fora do ar).")
                    continue
            else:
                indice_no = int(escolha)
                if indice_no < 0 or indice_no >= len(nos):
                    print("Índice inválido.")
                    continue
                
            sql = input("Digite a query SQL: ")
            if not sql:
                continue
                
            resultado = enviar_query(nos[indice_no], sql)
            
            print("\n--- Resultado ---")
            print(json.dumps(resultado, indent=2))
            print("--------------")
            
        except ValueError:
            print("Por favor, insira uma opção válida.")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    principal()