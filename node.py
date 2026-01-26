import socket
import threading
import json
import time
import hashlib
import mysql.connector
from mysql.connector import Error
import sys
import os

class No:
    def __init__(self, id_no, caminho_config='config.json'):
        self.id_no = id_no
        self.carregar_configuracao(caminho_config)
        self.eu = self.info_nos[id_no]
        self.outros_nos = [n for n in self.info_nos if n['id'] != id_no]
        
        # Configuração do Banco de Dados
        self.config_bd = {
            'host': '127.0.0.1',  # Sempre usar localhost para DB
            'user': 'root',
            'password': 'root',
            'database': 'bd-dist',
            'port': self.eu['db_port'],
            'connect_timeout': 5
        }
        
        print(f"[Nó {self.id_no}] Iniciado com estratégia de Conexão Sob Demanda na porta DB {self.eu['db_port']}")

        self.id_coordenador = None
        self.nos_vivos = {self.id_no: time.time()}
        self.em_execucao = True
        self.lock = threading.Lock()
        
        # Iniciar threads de serviço
        self.iniciar_servicos()

    def carregar_configuracao(self, caminho):
        with open(caminho, 'r') as f:
            self.info_nos = json.load(f)['nodes']

    def criar_conexao(self):
        """Cria uma nova conexão com o banco de dados."""
        try:
            conn = mysql.connector.connect(**self.config_bd)
            if conn.is_connected():
                conn.autocommit = True
                return conn
        except Error as e:
            print(f"[Nó {self.id_no}] Erro ao conectar ao MySQL (Porta {self.eu['db_port']}): {e}")
        return None

    def calcular_checksum(self, dados):
        return hashlib.md5(dados.encode()).hexdigest()

    def enviar_msg(self, no_alvo, msg):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((no_alvo['ip'], no_alvo['port']))
                s.sendall(json.dumps(msg).encode())
        except Exception as e:
            # Silencia heartbeats para não poluir o log, mas registra erros de replicação e eleição
            if msg.get('type') not in ['HEARTBEAT']:
                print(f"[Nó {self.id_no}] Erro ao enviar {msg.get('type')} para Nó {no_alvo['id']} ({no_alvo['ip']}): {e}")

    def realizar_broadcast(self, msg):
        if msg.get('type') != 'HEARTBEAT': # Evita spam de heartbeat
            print(f"[Nó {self.id_no}] >>> INICIANDO BROADCAST: {msg.get('type')} <<<", flush=True)
        
        for no in self.outros_nos:
            if msg.get('type') != 'HEARTBEAT':
                print(f"[Nó {self.id_no}] -> Enviando para Nó {no['id']} ({no['ip']}:{no['port']})", flush=True)
            self.enviar_msg(no, msg)

    def iniciar_servicos(self):
        threading.Thread(target=self.executar_servidor, daemon=True).start()
        threading.Thread(target=self.enviar_heartbeat, daemon=True).start()
        threading.Thread(target=self.monitorar_nos, daemon=True).start()
        self.iniciar_eleicao()

    def executar_servidor(self):
        print(f"[Nó {self.id_no}] Iniciando thread do servidor...", flush=True)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Sempre escuta em todas as interfaces (0.0.0.0) para aceitar conexões externas
            # O IP configurado em self.eu['ip'] é usado apenas para comunicação entre nós
            sock.bind(('0.0.0.0', self.eu['port']))
            sock.listen(10)
            sock.settimeout(1.0)
            print(f"[Nó {self.id_no}] Servidor escutando na porta {self.eu['port']}", flush=True)
            counter = 0
            while self.em_execucao:
                try:
                    counter += 1
                    if counter % 10 == 0:
                        print(f"[Nó {self.id_no}] Server loop iteration {counter}, em_execucao={self.em_execucao}", flush=True)
                    conn, addr = sock.accept()
                    print(f"[Nó {self.id_no}] Conexão aceita de {addr}", flush=True)
                    threading.Thread(target=self.tratar_cliente, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.em_execucao: print(f"[Nó {self.id_no}] Erro no socket: {e}", flush=True)
        except Exception as e:
            print(f"[Nó {self.id_no}] Erro fatal no servidor: {e}", flush=True)
            import traceback
            traceback.print_exc()

    def tratar_cliente(self, conn):
        try:
            dados = conn.recv(8192)
            if not dados: 
                print(f"[Nó {self.id_no}] Nenhum dado recebido do cliente", flush=True)
                conn.close()
                return
            msg = json.loads(dados.decode())
            print(f"[Nó {self.id_no}] Mensagem recebida: {msg.get('type')}", flush=True)
            if msg.get('type') == 'CLIENT_QUERY':
                resposta = self.executar_query(msg['sql'])
                print(f"[Nó {self.id_no}] Enviando resposta: {resposta.get('status')}", flush=True)
                conn.sendall(json.dumps(resposta).encode())
            elif msg.get('type') == 'GET_COORDINATOR':
                resposta = {'status': 'success', 'coordinator_id': self.id_coordenador}
                conn.sendall(json.dumps(resposta).encode())
            else:
                self.processar_mensagem(msg)
        except Exception as e:
            print(f"[Nó {self.id_no}] Erro ao tratar cliente: {e}", flush=True)
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    def processar_mensagem(self, msg):
        tipo_msg = msg.get('type')
        if tipo_msg == 'HEARTBEAT':
            with self.lock: self.nos_vivos[msg['id']] = time.time()
        elif tipo_msg == 'ELECTION':
            if msg['id'] < self.id_no:
                remetente = next(n for n in self.info_nos if n['id'] == msg['id'])
                self.enviar_msg(remetente, {'type': 'ELECTION_OK', 'id': self.id_no})
                self.iniciar_eleicao()
        elif tipo_msg == 'COORDINATOR':
            with self.lock:
                self.id_coordenador = msg['id']
                print(f"[Nó {self.id_no}] Novo Coordenador: {self.id_coordenador}")
        elif tipo_msg == 'REPLICATE':
            self.executar_query_replicada(msg)

    def enviar_heartbeat(self):
        while self.em_execucao:
            self.realizar_broadcast({'type': 'HEARTBEAT', 'id': self.id_no})
            time.sleep(2)

    def monitorar_nos(self):
        while self.em_execucao:
            time.sleep(5)
            agora = time.time()
            with self.lock:
                nos_mortos = [nid for nid, visto in self.nos_vivos.items() 
                              if agora - visto > 10 and nid != self.id_no]
                for nid in nos_mortos:
                    print(f"[Nó {self.id_no}] Nó {nid} offline")
                    del self.nos_vivos[nid]
                    if self.id_coordenador == nid:
                        self.id_coordenador = None
                        self.iniciar_eleicao()

    def iniciar_eleicao(self):
        print(f"[Nó {self.id_no}] Iniciando eleição...")
        superiores = [n for n in self.outros_nos if n['id'] > self.id_no]
        if not superiores:
            self.id_coordenador = self.id_no
            self.realizar_broadcast({'type': 'COORDINATOR', 'id': self.id_no})
            print(f"[Nó {self.id_no}] Eu sou o coordenador")
        else:
            for n in superiores: self.enviar_msg(n, {'type': 'ELECTION', 'id': self.id_no})
            time.sleep(2.0)
            if self.id_coordenador is None:
                self.id_coordenador = self.id_no
                self.realizar_broadcast({'type': 'COORDINATOR', 'id': self.id_no})

    def executar_query(self, sql):
        eh_escrita = any(p in sql.upper() for p in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"])
        checksum = self.calcular_checksum(sql)
        print(f"[Nó {self.id_no}] Executando Query: {sql}")
        
        # Conexão Sob Demanda
        conn = self.criar_conexao()
        if not conn: 
            return {"status": "error", "node": self.id_no, "message": "Falha ao conectar ao Banco de Dados"}
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql)
            resultado = cursor.fetchall() if not eh_escrita else None
            conn.commit()
            
            if eh_escrita:
                print(f"[Nó {self.id_no}] Replicando Checksum: {checksum}")
                self.realizar_broadcast({
                    'type': 'REPLICATE', 'sql': sql, 'checksum': checksum, 'origin': self.id_no
                })
            return {"status": "success", "node": self.id_no, "data": resultado}
        except Error as e:
            print(f"[Nó {self.id_no}] Erro SQL: {e}")
            return {"status": "error", "node": self.id_no, "message": str(e)}
        finally:
            if conn: conn.close()

    def executar_query_replicada(self, msg):
        if self.calcular_checksum(msg['sql']) != msg['checksum']: 
            print(f"[Nó {self.id_no}] Checksum inválido na replicação")
            return
            
        conn = self.criar_conexao()
        if not conn: return
        try:
            print(f"[Nó {self.id_no}] Aplicando replicação do Nó {msg['origin']}")
            cursor = conn.cursor()
            cursor.execute(msg['sql'])
            conn.commit()
        except Error as e:
            print(f"[Nó {self.id_no}] Erro na replicação: {e}")
        finally:
            if conn: conn.close()

    def parar(self):
        self.em_execucao = False
        print(f"[Nó {self.id_no}] Parado.")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    id_no_args = int(sys.argv[1])
    caminho_config = sys.argv[2] if len(sys.argv) > 2 else 'config.json'
    
    # Configuração de logs removida para exibir output no console
    # dir_logs = "logs"
    # ... (código de log removido)
    
    no = No(id_no_args, caminho_config)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        no.parar()

