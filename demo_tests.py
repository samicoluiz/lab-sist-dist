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

def carregar_configuracao():
    with open('config.json', 'r') as f:
        return json.load(f)['nodes']

def enviar_query(info_no, sql):
    """Envia query para um nó específico e retorna resultado"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((info_no['ip'], info_no['port']))
            msg = {'type': 'CLIENT_QUERY', 'sql': sql}
            s.sendall(json.dumps(msg).encode())
            
            dados = s.recv(16384)
            if dados:
                return json.loads(dados.decode())
    except Exception as e:
        return {"status": "error", "message": str(e), "node": info_no['id']}

def imprimir_separador(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")

def imprimir_resultado(resultado):
    print(f"  Status: {resultado.get('status')}")
    print(f"  Nó Executor: {resultado.get('node')}")
    if resultado.get('data'):
        print(f"  Dados: {json.dumps(resultado['data'], indent=4)}")
    if resultado.get('message'):
        print(f"  Mensagem: {resultado['message']}")

def verificar_no_vivo(no):
    """Verifica se um nó está respondendo"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((no['ip'], no['port']))
            return True
    except:
        return False

def testar_conectividade(nos):
    """TESTE 1: Verifica conectividade com todos os nós"""
    imprimir_separador("TESTE 1: Verificação de Conectividade")
    
    todos_vivos = True
    for no in nos:
        vivo = verificar_no_vivo(no)
        status = "✅ ONLINE" if vivo else "❌ OFFLINE"
        print(f"  Nó {no['id']} ({no['ip']}:{no['port']}): {status}")
        if not vivo:
            todos_vivos = False
    
    return todos_vivos

def testar_replicacao(nos):
    """TESTE 2: Testa replicação de escrita"""
    imprimir_separador("TESTE 2: Replicação de Escrita (INSERT)")
    
    # Limpa tabela primeiro
    print("\n  [1/4] Limpando tabela users em todos os nós...")
    for no in nos:
        enviar_query(no, "DELETE FROM users")
    time.sleep(1)
    
    # Insere via Nó 0
    nome_teste = f"Usuario_Teste_{int(time.time())}"
    email_teste = f"teste_{int(time.time())}@demo.com"
    sql = f"INSERT INTO users (name, email) VALUES ('{nome_teste}', '{email_teste}')"
    
    print(f"\n  [2/4] Enviando INSERT para Nó 0:")
    print(f"        SQL: {sql}")
    resultado = enviar_query(nos[0], sql)
    imprimir_resultado(resultado)
    
    # Aguarda replicação
    print("\n  [3/4] Aguardando replicação (2 segundos)...")
    time.sleep(2)
    
    # Verifica em todos os nós
    print("\n  [4/4] Verificando dados em cada nó:")
    sql_select = "SELECT * FROM users"
    
    tudo_consistente = True
    for no in nos:
        resultado = enviar_query(no, sql_select)
        print(f"\n  --- Nó {no['id']} ---")
        imprimir_resultado(resultado)
        
        if resultado.get('status') == 'success':
            dados = resultado.get('data', [])
            tem_registro = any(r.get('name') == nome_teste for r in dados)
            if tem_registro:
                print(f"  ✅ Registro '{nome_teste}' encontrado!")
            else:
                print(f"  ❌ Registro '{nome_teste}' NÃO encontrado!")
                tudo_consistente = False
    
    return tudo_consistente

def testar_balanceamento_carga(nos, num_requisicoes=9):
    """TESTE 3: Demonstra balanceamento de carga"""
    imprimir_separador("TESTE 3: Balanceamento de Carga")
    
    print(f"\n  Enviando {num_requisicoes} queries SELECT com seleção aleatória de nó...")
    
    contagem_no = {n['id']: 0 for n in nos}
    
    for i in range(num_requisicoes):
        no_selecionado = random.choice(nos)
        resultado = enviar_query(no_selecionado, "SELECT COUNT(*) as total FROM users")
        
        if resultado.get('status') == 'success':
            contagem_no[no_selecionado['id']] += 1
            print(f"  Requisição {i+1}: Nó {no_selecionado['id']} ✅")
        else:
            print(f"  Requisição {i+1}: Nó {no_selecionado['id']} ❌ {resultado.get('message', 'erro')}")
    
    print("\n  Distribuição de requisições:")
    for id_no, contagem in contagem_no.items():
        barra = "█" * contagem
        print(f"    Nó {id_no}: {barra} ({contagem} requisições)")
    
    return True

def testar_consistencia(nos):
    """TESTE 4: Verifica consistência entre nós"""
    imprimir_separador("TESTE 4: Consistência de Dados Entre Nós")
    
    sql = "SELECT * FROM users ORDER BY id"
    resultados = []
    
    for no in nos:
        resultado = enviar_query(no, sql)
        print(f"\n  Nó {no['id']}:")
        
        if resultado.get('status') == 'success':
            dados = resultado.get('data', [])
            print(f"    Registros: {len(dados)}")
            resultados.append(dados)
        else:
            print(f"    Erro: {resultado.get('message')}")
            resultados.append(None)
    
    # Compara resultados
    if all(r is not None for r in resultados):
        if all(r == resultados[0] for r in resultados):
            print("\n  ✅ TODOS OS NÓS TÊM DADOS IDÊNTICOS!")
            return True
        else:
            print("\n  ❌ INCONSISTÊNCIA DETECTADA!")
            return False
    return False

def testar_multiplas_escritas(nos):
    """TESTE 5: Múltiplas escritas em sequência"""
    imprimir_separador("TESTE 5: Múltiplas Escritas em Sequência")
    
    # Limpa primeiro
    for no in nos:
        enviar_query(no, "DELETE FROM users")
    time.sleep(1)
    
    # Insere em nós diferentes
    dados_teste = [
        (0, "Alice", "alice@test.com"),
        (1, "Bob", "bob@test.com"),
        (2, "Carol", "carol@test.com"),
    ]
    
    print("\n  Inserindo dados em nós diferentes:")
    for indice_no, nome, email in dados_teste:
        if indice_no < len(nos):
            sql = f"INSERT INTO users (name, email) VALUES ('{nome}', '{email}')"
            resultado = enviar_query(nos[indice_no], sql)
            status = "✅" if resultado.get('status') == 'success' else "❌"
            print(f"    Nó {indice_no}: INSERT {nome} {status}")
            time.sleep(0.5)
    
    print("\n  Aguardando replicação (3 segundos)...")
    time.sleep(3)
    
    # Verifica
    print("\n  Verificando em Nó 0:")
    resultado = enviar_query(nos[0], "SELECT name, email FROM users ORDER BY name")
    if resultado.get('status') == 'success':
        for linha in resultado.get('data', []):
            print(f"    - {linha['name']}: {linha['email']}")
        
        if len(resultado.get('data', [])) == 3:
            print("\n  ✅ TODOS OS 3 REGISTROS REPLICADOS!")
            return True
    
    return False

def testar_update_delete(nos):
    """TESTE 6: UPDATE e DELETE replicados"""
    imprimir_separador("TESTE 6: UPDATE e DELETE Replicados")
    
    # UPDATE
    print("\n  [1/2] Testando UPDATE...")
    sql_update = "UPDATE users SET email = 'alice_updated@test.com' WHERE name = 'Alice'"
    resultado = enviar_query(nos[1], sql_update)  # Envia pro nó 1
    status = "✅" if resultado.get('status') == 'success' else "❌"
    print(f"    UPDATE enviado para Nó 1: {status}")
    
    time.sleep(2)
    
    # Verifica no nó 0
    resultado = enviar_query(nos[0], "SELECT email FROM users WHERE name = 'Alice'")
    if resultado.get('status') == 'success' and resultado.get('data'):
        email = resultado['data'][0]['email']
        if 'updated' in email:
            print(f"    ✅ UPDATE replicado! Email no Nó 0: {email}")
        else:
            print(f"    ❌ UPDATE não replicou. Email: {email}")
    
    # DELETE
    print("\n  [2/2] Testando DELETE...")
    sql_delete = "DELETE FROM users WHERE name = 'Carol'"
    resultado = enviar_query(nos[2], sql_delete)  # Envia pro nó 2
    status = "✅" if resultado.get('status') == 'success' else "❌"
    print(f"    DELETE enviado para Nó 2: {status}")
    
    time.sleep(2)
    
    # Verifica no nó 0
    resultado = enviar_query(nos[0], "SELECT COUNT(*) as total FROM users WHERE name = 'Carol'")
    if resultado.get('status') == 'success' and resultado.get('data'):
        contagem = resultado['data'][0]['total']
        if contagem == 0:
            print(f"    ✅ DELETE replicado! Carol não existe no Nó 0")
            return True
        else:
            print(f"    ❌ DELETE não replicou. Carol ainda existe.")
    
    return False

def executar_todos_testes():
    """Executa todos os testes em sequência"""
    print("\n" + "="*60)
    print("  DEMONSTRAÇÃO DO MIDDLEWARE DE BANCO DE DADOS DISTRIBUÍDO")
    print("="*60)
    print(f"\n  Data/Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        nos = carregar_configuracao()
        print(f"  Nós configurados: {len(nos)}")
    except FileNotFoundError:
        print("  ❌ Erro: config.json não encontrado!")
        return
    
    resultados = {}
    
    # Teste 1: Conectividade
    if not testar_conectividade(nos):
        print("\n  ⚠️  ATENÇÃO: Nem todos os nós estão online.")
        print("  Certifique-se de que todos os nós estão rodando antes de continuar.")
        resposta = input("\n  Deseja continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            return
    
    # Filtra apenas nós online
    nos_online = [n for n in nos if verificar_no_vivo(n)]
    
    if len(nos_online) < 2:
        print("\n  ❌ Precisa de pelo menos 2 nós online para demonstrar replicação.")
        return
    
    # Executa testes
    resultados['Replicação'] = testar_replicacao(nos_online)
    resultados['Balanceamento'] = testar_balanceamento_carga(nos_online)
    resultados['Consistência'] = testar_consistencia(nos_online)
    
    if len(nos_online) >= 3:
        resultados['Múltiplas Escritas'] = testar_multiplas_escritas(nos_online)
        resultados['UPDATE/DELETE'] = testar_update_delete(nos_online)
    
    # Resumo
    imprimir_separador("RESUMO DOS TESTES")
    for nome_teste, passou in resultados.items():
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"  {nome_teste}: {status}")
    
    total_passou = sum(1 for v in resultados.values() if v)
    print(f"\n  Total: {total_passou}/{len(resultados)} testes passaram")
    
    print("\n" + "="*60)
    print("  FIM DA DEMONSTRAÇÃO")
    print("="*60 + "\n")

if __name__ == "__main__":
    executar_todos_testes()
