#!/usr/bin/env python3
"""
Script de Demonstração do Middleware de Banco de Dados Distribuído
Execute com: python demo_tests.py

Este script executa uma sequência de testes para demonstrar
todas as funcionalidades do bd-dist.
"""

import socket
import json
import time
import random
import sys

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)['nodes']

def send_query(node_info, sql):
    """Envia query para um nó específico e retorna resultado"""
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
        return {"status": "error", "message": str(e), "node": node_info['id']}

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(result):
    print(f"  Status: {result.get('status')}")
    print(f"  Nó Executor: {result.get('node')}")
    if result.get('data'):
        print(f"  Dados: {json.dumps(result['data'], indent=4)}")
    if result.get('message'):
        print(f"  Mensagem: {result['message']}")

def check_node_alive(node):
    """Verifica se um nó está respondendo"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((node['ip'], node['port']))
            return True
    except:
        return False

def test_connectivity(nodes):
    """TESTE 1: Verifica conectividade com todos os nós"""
    print_separator("TESTE 1: Verificação de Conectividade")
    
    all_alive = True
    for node in nodes:
        alive = check_node_alive(node)
        status = "✅ ONLINE" if alive else "❌ OFFLINE"
        print(f"  Nó {node['id']} ({node['ip']}:{node['port']}): {status}")
        if not alive:
            all_alive = False
    
    return all_alive

def test_replication(nodes):
    """TESTE 2: Testa replicação de escrita"""
    print_separator("TESTE 2: Replicação de Escrita (INSERT)")
    
    # Limpa tabela primeiro
    print("\n  [1/4] Limpando tabela users em todos os nós...")
    for node in nodes:
        send_query(node, "DELETE FROM users")
    time.sleep(1)
    
    # Insere via Nó 0
    test_name = f"Usuario_Teste_{int(time.time())}"
    test_email = f"teste_{int(time.time())}@demo.com"
    sql = f"INSERT INTO users (name, email) VALUES ('{test_name}', '{test_email}')"
    
    print(f"\n  [2/4] Enviando INSERT para Nó 0:")
    print(f"        SQL: {sql}")
    result = send_query(nodes[0], sql)
    print_result(result)
    
    # Aguarda replicação
    print("\n  [3/4] Aguardando replicação (2 segundos)...")
    time.sleep(2)
    
    # Verifica em todos os nós
    print("\n  [4/4] Verificando dados em cada nó:")
    select_sql = "SELECT * FROM users"
    
    all_consistent = True
    for node in nodes:
        result = send_query(node, select_sql)
        print(f"\n  --- Nó {node['id']} ---")
        print_result(result)
        
        if result.get('status') == 'success':
            data = result.get('data', [])
            has_record = any(r.get('name') == test_name for r in data)
            if has_record:
                print(f"  ✅ Registro '{test_name}' encontrado!")
            else:
                print(f"  ❌ Registro '{test_name}' NÃO encontrado!")
                all_consistent = False
    
    return all_consistent

def test_load_balancing(nodes, num_requests=9):
    """TESTE 3: Demonstra balanceamento de carga"""
    print_separator("TESTE 3: Balanceamento de Carga")
    
    print(f"\n  Enviando {num_requests} queries SELECT com seleção aleatória de nó...")
    
    node_count = {n['id']: 0 for n in nodes}
    
    for i in range(num_requests):
        selected_node = random.choice(nodes)
        result = send_query(selected_node, "SELECT COUNT(*) as total FROM users")
        
        if result.get('status') == 'success':
            node_count[selected_node['id']] += 1
            print(f"  Requisição {i+1}: Nó {selected_node['id']} ✅")
        else:
            print(f"  Requisição {i+1}: Nó {selected_node['id']} ❌ {result.get('message', 'erro')}")
    
    print("\n  Distribuição de requisições:")
    for node_id, count in node_count.items():
        bar = "█" * count
        print(f"    Nó {node_id}: {bar} ({count} requisições)")
    
    return True

def test_consistency(nodes):
    """TESTE 4: Verifica consistência entre nós"""
    print_separator("TESTE 4: Consistência de Dados Entre Nós")
    
    sql = "SELECT * FROM users ORDER BY id"
    results = []
    
    for node in nodes:
        result = send_query(node, sql)
        print(f"\n  Nó {node['id']}:")
        
        if result.get('status') == 'success':
            data = result.get('data', [])
            print(f"    Registros: {len(data)}")
            results.append(data)
        else:
            print(f"    Erro: {result.get('message')}")
            results.append(None)
    
    # Compara resultados
    if all(r is not None for r in results):
        if all(r == results[0] for r in results):
            print("\n  ✅ TODOS OS NÓS TÊM DADOS IDÊNTICOS!")
            return True
        else:
            print("\n  ❌ INCONSISTÊNCIA DETECTADA!")
            return False
    return False

def test_multiple_writes(nodes):
    """TESTE 5: Múltiplas escritas em sequência"""
    print_separator("TESTE 5: Múltiplas Escritas em Sequência")
    
    # Limpa primeiro
    for node in nodes:
        send_query(node, "DELETE FROM users")
    time.sleep(1)
    
    # Insere em nós diferentes
    test_data = [
        (0, "Alice", "alice@test.com"),
        (1, "Bob", "bob@test.com"),
        (2, "Carol", "carol@test.com"),
    ]
    
    print("\n  Inserindo dados em nós diferentes:")
    for node_idx, name, email in test_data:
        if node_idx < len(nodes):
            sql = f"INSERT INTO users (name, email) VALUES ('{name}', '{email}')"
            result = send_query(nodes[node_idx], sql)
            status = "✅" if result.get('status') == 'success' else "❌"
            print(f"    Nó {node_idx}: INSERT {name} {status}")
            time.sleep(0.5)
    
    print("\n  Aguardando replicação (3 segundos)...")
    time.sleep(3)
    
    # Verifica
    print("\n  Verificando em Nó 0:")
    result = send_query(nodes[0], "SELECT name, email FROM users ORDER BY name")
    if result.get('status') == 'success':
        for row in result.get('data', []):
            print(f"    - {row['name']}: {row['email']}")
        
        if len(result.get('data', [])) == 3:
            print("\n  ✅ TODOS OS 3 REGISTROS REPLICADOS!")
            return True
    
    return False

def test_update_delete(nodes):
    """TESTE 6: UPDATE e DELETE replicados"""
    print_separator("TESTE 6: UPDATE e DELETE Replicados")
    
    # UPDATE
    print("\n  [1/2] Testando UPDATE...")
    update_sql = "UPDATE users SET email = 'alice_updated@test.com' WHERE name = 'Alice'"
    result = send_query(nodes[1], update_sql)  # Envia pro nó 1
    status = "✅" if result.get('status') == 'success' else "❌"
    print(f"    UPDATE enviado para Nó 1: {status}")
    
    time.sleep(2)
    
    # Verifica no nó 0
    result = send_query(nodes[0], "SELECT email FROM users WHERE name = 'Alice'")
    if result.get('status') == 'success' and result.get('data'):
        email = result['data'][0]['email']
        if 'updated' in email:
            print(f"    ✅ UPDATE replicado! Email no Nó 0: {email}")
        else:
            print(f"    ❌ UPDATE não replicou. Email: {email}")
    
    # DELETE
    print("\n  [2/2] Testando DELETE...")
    delete_sql = "DELETE FROM users WHERE name = 'Carol'"
    result = send_query(nodes[2], delete_sql)  # Envia pro nó 2
    status = "✅" if result.get('status') == 'success' else "❌"
    print(f"    DELETE enviado para Nó 2: {status}")
    
    time.sleep(2)
    
    # Verifica no nó 0
    result = send_query(nodes[0], "SELECT COUNT(*) as total FROM users WHERE name = 'Carol'")
    if result.get('status') == 'success' and result.get('data'):
        count = result['data'][0]['total']
        if count == 0:
            print(f"    ✅ DELETE replicado! Carol não existe no Nó 0")
            return True
        else:
            print(f"    ❌ DELETE não replicou. Carol ainda existe.")
    
    return False

def run_all_tests():
    """Executa todos os testes em sequência"""
    print("\n" + "="*60)
    print("  DEMONSTRAÇÃO DO MIDDLEWARE DE BANCO DE DADOS DISTRIBUÍDO")
    print("="*60)
    print(f"\n  Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        nodes = load_config()
        print(f"  Nós configurados: {len(nodes)}")
    except FileNotFoundError:
        print("  ❌ Erro: config.json não encontrado!")
        return
    
    results = {}
    
    # Teste 1: Conectividade
    if not test_connectivity(nodes):
        print("\n  ⚠️  ATENÇÃO: Nem todos os nós estão online.")
        print("  Certifique-se de que todos os nós estão rodando antes de continuar.")
        response = input("\n  Deseja continuar mesmo assim? (s/n): ")
        if response.lower() != 's':
            return
    
    # Filtra apenas nós online
    online_nodes = [n for n in nodes if check_node_alive(n)]
    
    if len(online_nodes) < 2:
        print("\n  ❌ Precisa de pelo menos 2 nós online para demonstrar replicação.")
        return
    
    # Executa testes
    results['Replicação'] = test_replication(online_nodes)
    results['Balanceamento'] = test_load_balancing(online_nodes)
    results['Consistência'] = test_consistency(online_nodes)
    
    if len(online_nodes) >= 3:
        results['Múltiplas Escritas'] = test_multiple_writes(online_nodes)
        results['UPDATE/DELETE'] = test_update_delete(online_nodes)
    
    # Resumo
    print_separator("RESUMO DOS TESTES")
    for test_name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {test_name}: {status}")
    
    total_passed = sum(1 for v in results.values() if v)
    print(f"\n  Total: {total_passed}/{len(results)} testes passaram")
    
    print("\n" + "="*60)
    print("  FIM DA DEMONSTRAÇÃO")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_all_tests()