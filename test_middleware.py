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

from node import Node

class TestDistDB(unittest.TestCase):
    def setUp(self):
        self.nodes = []
        self.mock_conns = []
        self.mock_cursors = []
        self.config_file = f"test_config_{threading.get_ident()}.json"

    def tearDown(self):
        for node in self.nodes:
            node.stop()
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        time.sleep(1)

    def create_nodes_with_config(self, node_ids, base_port):
        nodes_info = []
        for i in node_ids:
            nodes_info.append({"id": i, "ip": "127.0.0.1", "port": base_port + i, "db_port": 3306 + i})
        
        with open(self.config_file, 'w') as f:
            json.dump({"nodes": nodes_info}, f)

        created_nodes = []
        for i in node_ids:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_conn.is_connected.return_value = True
            self.mock_conns.append(mock_conn)
            self.mock_cursors.append(mock_cursor)
            
            with patch('mysql.connector.connect', return_value=mock_conn):
                node = Node(i, config_path=self.config_file)
                self.nodes.append(node)
                created_nodes.append(node)
        return created_nodes

    def test_election_and_coordinator(self):
        print("\n--- Testando Eleição ---")
        base_port = 7000
        created = self.create_nodes_with_config([0, 1, 2], base_port)
        n0, n1, n2 = created

        time.sleep(5)

        print(f"Coordenador do Nó 0: {n0.coordinator_id}")
        print(f"Coordenador do Nó 1: {n1.coordinator_id}")
        print(f"Coordenador do Nó 2: {n2.coordinator_id}")

        self.assertEqual(n0.coordinator_id, 2)
        self.assertEqual(n1.coordinator_id, 2)
        self.assertEqual(n2.coordinator_id, 2)

    def test_replication(self):
        print("\n--- Testando Replicação ---")
        base_port = 8000
        created = self.create_nodes_with_config([0, 1, 2], base_port)
        n0, n1, n2 = created
        
        time.sleep(3)

        sql = "INSERT INTO users (name) VALUES ('Teste')"
        print(f"Executando '{sql}' no Nó 0")
        response = n0.execute_query(sql)

        self.assertEqual(response['status'], 'success')
        time.sleep(2)

        self.mock_cursors[0].execute.assert_called_with(sql)
        
        found_n1 = any(call.args[0] == sql for call in self.mock_cursors[1].execute.call_args_list)
        found_n2 = any(call.args[0] == sql for call in self.mock_cursors[2].execute.call_args_list)
        
        print(f"Replicado para o Nó 1: {found_n1}")
        print(f"Replicado para o Nó 2: {found_n2}")

        self.assertTrue(found_n1)
        self.assertTrue(found_n2)

    def test_read_operation(self):
        print("\n--- Testando Operação de Leitura ---")
        base_port = 9000
        created = self.create_nodes_with_config([0, 1], base_port)
        n0, n1 = created
        
        time.sleep(2)
        self.mock_cursors[0].fetchall.return_value = [{'id': 1, 'name': 'Luiz'}]

        sql = "SELECT * FROM users"
        print(f"Executando '{sql}' no Nó 0")
        response = n0.execute_query(sql)

        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['data'], [{'id': 1, 'name': 'Luiz'}])
        
        self.mock_cursors[1].reset_mock()
        time.sleep(1)
        self.mock_cursors[1].execute.assert_not_called()
        print("Operação de leitura corretamente NÃO replicada.")

if __name__ == '__main__':
    unittest.main()