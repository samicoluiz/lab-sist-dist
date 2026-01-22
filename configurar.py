# -*- coding: utf-8 -*-

"""
Script de Configuração do Ambiente Distribuído

Este script gera o arquivo `config.json` necessário para o middleware,
com base nos endereços de IP fornecidos como argumentos.

Uso:
  python configurar.py <ip_node_0> <ip_node_1> <ip_node_2> ...

Exemplo:
  python configurar.py 192.168.1.10 192.168.1.11 192.168.1.12
"""

import sys
import json

def gerar_config(ips):
    """
    Gera a estrutura de configuração dos nós.

    Args:
        ips (list): Uma lista de strings contendo os endereços IP dos nós.

    Returns:
        dict: Um dicionário contendo a configuração formatada.
    """
    if not ips:
        print("Erro: Nenhum endereço IP foi fornecido.")
        print(__doc__)
        sys.exit(1)

    nodes_config = []
    base_port = 5000
    # Portas do Docker: db1->3309 (evita conflito com 3306 local), db2->3307, db3->3308
    db_ports = [3309, 3307, 3308]

    for i, ip in enumerate(ips):
        # Se houver mais IPs que portas definidas, recicla (apenas fallback)
        porta_db = db_ports[i % len(db_ports)]
        
        node_info = {
            "id": i,
            "ip": ip,
            "port": base_port + i,
            "db_port": porta_db
        }
        nodes_config.append(node_info)

    return {"nodes": nodes_config}

def salvar_arquivo(config, nome_arquivo="config.json"):
    """
    Salva a configuração em um arquivo JSON.

    Args:
        config (dict): O dicionário de configuração a ser salvo.
        nome_arquivo (str): O nome do arquivo a ser gerado.
    """
    try:
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Sucesso: Arquivo '{nome_arquivo}' gerado com {len(config['nodes'])} nós.")
        print("Conteúdo do arquivo:")
        print(json.dumps(config, indent=2))
    except IOError as e:
        print(f"Erro ao salvar o arquivo '{nome_arquivo}': {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Os argumentos começam do índice 1, pois o índice 0 é o nome do script
    enderecos_ip = sys.argv[1:]
    
    configuracao = gerar_config(enderecos_ip)
    salvar_arquivo(configuracao)
