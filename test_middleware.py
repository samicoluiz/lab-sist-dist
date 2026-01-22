import unittest
from unittest.mock import MagicMock, patch
import threading
import time
import json
import socket
import os
import sys

# Adiciona o diretório pai ao sys.path para importar o node
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from node import No

class TesteBancoDistribuido(unittest.TestCase):
    def setUp(self):
        self.nos = []
        self.mock_conns = []
        self.mock_cursors = []
        self.arquivo_config = f"test_config_{threading.get_ident()}.json"

    def tearDown(self):
        for no in self.nos:
            no.parar()
        if os.path.exists(self.arquivo_config):
            os.remove(self.arquivo_config)
        time.sleep(1)

    def criar_nos_com_config(self, ids_nos, porta_base):
        info_nos = []
        for i in ids_nos:
            info_nos.append({"id": i, "ip": "127.0.0.1", "port": porta_base + i, "db_port": 3306 + i})
        
        with open(self.arquivo_config, 'w') as f:
            json.dump({"nodes": info_nos}, f)

        nos_criados = []
        for i in ids_nos:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.is_connected.return_value = True
            self.mock_conns.append(mock_conn)
            self.mock_cursors.append(mock_cursor)
            
            with patch('mysql.connector.connect', return_value=mock_conn):
                no = No(i, caminho_config=self.arquivo_config)
                self.nos.append(no)
                nos_criados.append(no)
        return nos_criados

    def test_eleicao_e_coordenador(self):
        print("\n--- Testando Eleição ---")
        porta_base = 7000
        criados = self.criar_nos_com_config([0, 1, 2], porta_base)
        n0, n1, n2 = criados

        time.sleep(5)

        print(f"Coordenador do Nó 0: {n0.id_coordenador}")
        print(f"Coordenador do Nó 1: {n1.id_coordenador}")
        print(f"Coordenador do Nó 2: {n2.id_coordenador}")

        self.assertEqual(n0.id_coordenador, 2)
        self.assertEqual(n1.id_coordenador, 2)
        self.assertEqual(n2.id_coordenador, 2)

    def test_replicacao(self):
        print("\n--- Testando Replicação ---")
        porta_base = 8000
        criados = self.criar_nos_com_config([0, 1, 2], porta_base)
        n0, n1, n2 = criados
        
        time.sleep(3)

        sql = "INSERT INTO users (name) VALUES ('Teste')"
        print(f"Executando '{sql}' no Nó 0")
        resposta = n0.executar_query(sql)

        self.assertEqual(resposta['status'], 'success')
        time.sleep(2)

        self.mock_cursors[0].execute.assert_called_with(sql)
        
        encontrado_n1 = any(call.args[0] == sql for call in self.mock_cursors[1].execute.call_args_list)
        encontrado_n2 = any(call.args[0] == sql for call in self.mock_cursors[2].execute.call_args_list)
        
        print(f"Replicado para o Nó 1: {encontrado_n1}")
        print(f"Replicado para o Nó 2: {encontrado_n2}")

        self.assertTrue(encontrado_n1)
        self.assertTrue(encontrado_n2)

    def test_operacao_leitura(self):
        print("\n--- Testando Operação de Leitura ---")
        porta_base = 9000
        criados = self.criar_nos_com_config([0, 1], porta_base)
        n0, n1 = criados
        
        time.sleep(2)
        self.mock_cursors[0].fetchall.return_value = [{'id': 1, 'name': 'Luiz'}]

        sql = "SELECT * FROM users"
        print(f"Executando '{sql}' no Nó 0")
        resposta = n0.executar_query(sql)

        self.assertEqual(resposta['status'], 'success')
        self.assertEqual(resposta['data'], [{'id': 1, 'name': 'Luiz'}])
        
        self.mock_cursors[1].reset_mock()
        time.sleep(1)
        self.mock_cursors[1].execute.assert_not_called()
        print("Operação de leitura corretamente NÃO replicada.")

if __name__ == '__main__':
    unittest.main()
