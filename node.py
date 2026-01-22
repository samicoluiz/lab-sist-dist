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
        
        self.config_bd = {
            'host': self.eu['ip'],
            'user': 'root',
            'password': 'root',
            'database': 'bd-dist',
            'port': self.eu['db_port']
        }
        
        self.id_coordenador = None
        self.nos_vivos = {self.id_no: time.time()}
        self.em_execucao = True
        
        # Lock para operações thread-safe no estado
        self.lock = threading.Lock()
        
        # Conectar ao MySQL
        self.conexao_bd = self.conectar_bd()
        
        # Iniciar thread do servidor
        self.thread_servidor = threading.Thread(target=self.executar_servidor)
        self.thread_servidor.daemon = True
        self.thread_servidor.start()
        
        # Iniciar thread de heartbeat
        self.thread_hb = threading.Thread(target=self.enviar_heartbeat)
        self.thread_hb.daemon = True
        self.thread_hb.start()
        
        # Iniciar thread de monitoramento para verificar saúde dos nós e iniciar eleição
        self.thread_monitor = threading.Thread(target=self.monitorar_nos)
        self.thread_monitor.daemon = True
        self.thread_monitor.start()
        
        # Eleição inicial
        self.iniciar_eleicao()

    def carregar_configuracao(self, caminho):
        with open(caminho, 'r') as f:
            self.info_nos = json.load(f)['nodes']

    def conectar_bd(self):
        while self.em_execucao:
            try:
                conn = mysql.connector.connect(**self.config_bd)
                if conn.is_connected():
                    print(f"[Nó {self.id_no}] Conectado ao MySQL na porta {self.eu['db_port']}")
                    conn.autocommit = True
                    return conn
            except Error as e:
                print(f"[Nó {self.id_no}] Erro de Conexão MySQL: {e}. Retentando...")
                time.sleep(5)
        return None

    def calcular_checksum(self, dados):
        return hashlib.md5(dados.encode()).hexdigest()

    def enviar_msg(self, no_alvo, msg):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((no_alvo['ip'], no_alvo['port']))
                s.sendall(json.dumps(msg).encode())
        except Exception:
            # Nó pode estar fora do ar
            pass

    def realizar_broadcast(self, msg):
        for no in self.outros_nos:
            self.enviar_msg(no, msg)

    def executar_servidor(self):
        self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_servidor.bind((self.eu['ip'], self.eu['port']))
        self.socket_servidor.listen(5)
        print(f"[Nó {self.id_no}] Escutando em {self.eu['ip']}:{self.eu['port']}")
        
        self.socket_servidor.settimeout(1.0)
        while self.em_execucao:
            try:
                conn, addr = self.socket_servidor.accept()
                threading.Thread(target=self.tratar_cliente, args=(conn,)).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.em_execucao:
                    print(f"[Nó {self.id_no}] Erro no servidor: {e}")

    def parar(self):
        self.em_execucao = False
        if hasattr(self, 'socket_servidor'):
            self.socket_servidor.close()
        if self.conexao_bd:
            self.conexao_bd.close()
        print(f"[Nó {self.id_no}] Parado.")

    def tratar_cliente(self, conn):
        """
        Lida com conexões de entrada de outros nós ou clientes.
        Processa a mensagem e envia uma resposta se necessário.
        """
        try:
            with conn:
                dados = conn.recv(8192)
                if not dados:
                    return
                msg = json.loads(dados.decode())
                
                # Tratar Queries de Cliente/Externas
                if msg.get('type') == 'CLIENT_QUERY':
                    resposta = self.executar_query(msg['sql'])
                    conn.sendall(json.dumps(resposta).encode())
                
                elif msg.get('type') == 'GET_COORDINATOR':
                    resposta = {'status': 'success', 'coordinator_id': self.id_coordenador}
                    conn.sendall(json.dumps(resposta).encode())
                
                # Tratar Mensagens Internas
                else:
                    self.processar_mensagem(msg)
                    
        except Exception as e:
            print(f"[Nó {self.id_no}] Erro ao processar mensagem: {e}")

    def processar_mensagem(self, msg):
        tipo_msg = msg.get('type')
        
        if tipo_msg == 'HEARTBEAT':
            with self.lock:
                self.nos_vivos[msg['id']] = time.time()
                
        elif tipo_msg == 'ELECTION':
            if msg['id'] < self.id_no:
                # Responder OK e iniciar própria eleição
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
                nos_mortos = [nid for nid, visto_por_ultimo in self.nos_vivos.items() 
                              if agora - visto_por_ultimo > 10 and nid != self.id_no]
                for nid in nos_mortos:
                    print(f"[Nó {self.id_no}] Nó {nid} está fora do ar")
                    del self.nos_vivos[nid]
                    if self.id_coordenador == nid:
                        self.id_coordenador = None
                        self.iniciar_eleicao()

    def iniciar_eleicao(self):
        print(f"[Nó {self.id_no}] Iniciando eleição...")
        nos_superiores = [n for n in self.outros_nos if n['id'] > self.id_no]
        if not nos_superiores:
            # Eu sou o maior, eu sou o coordenador
            self.id_coordenador = self.id_no
            self.realizar_broadcast({'type': 'COORDINATOR', 'id': self.id_no})
            print(f"[Nó {self.id_no}] Eu sou o coordenador")
        else:
            for n in nos_superiores:
                self.enviar_msg(n, {'type': 'ELECTION', 'id': self.id_no})
            
            # Aguardar por OK
            time.sleep(2.0)
            
            # Se após esperar, eu ainda não sei quem é o coordenador,
            # e não recebi mensagem 'COORDINATOR' de alguém maior,
            # significa que os nós maiores morreram. Eu assumo.
            if self.id_coordenador is None:
                print(f"[Nó {self.id_no}] Nenhum nó superior respondeu. Eu estou assumindo!")
                self.id_coordenador = self.id_no
                self.realizar_broadcast({'type': 'COORDINATOR', 'id': self.id_no})

    def executar_query(self, sql):
        # Determinar se é WRITE (escrita) ou READ (leitura)
        eh_escrita = any(palavra in sql.upper() for palavra in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"])
        
        checksum = self.calcular_checksum(sql)
        print(f"[Nó {self.id_no}] QUERY RECEBIDA: {sql}")
        
        try:
            cursor = self.conexao_bd.cursor(dictionary=True)
            cursor.execute(sql)
            
            resultado = None
            if not eh_escrita:
                resultado = cursor.fetchall()
                print(f"[Nó {self.id_no}] Operação de LEITURA executada localmente. Linhas retornadas: {len(resultado)}")
            
            if eh_escrita:
                # Replicar
                print(f"[Nó {self.id_no}] Operação de ESCRITA. Transmitindo conteúdo para replicação...")
                print(f"[Nó {self.id_no}] Checksum: {checksum}")
                self.realizar_broadcast({
                    'type': 'REPLICATE',
                    'sql': sql,
                    'checksum': checksum,
                    'origin': self.id_no
                })
                print(f"[Nó {self.id_no}] Broadcast de replicação finalizado.")
            
            return {"status": "success", "node": self.id_no, "data": resultado}
        except Error as e:
            print(f"[Nó {self.id_no}] Erro SQL: {e}")
            return {"status": "error", "node": self.id_no, "message": str(e)}

    def executar_query_replicada(self, msg):
        sql = msg['sql']
        checksum_recebido = msg['checksum']
        
        # Verificar integridade
        if self.calcular_checksum(sql) != checksum_recebido:
            print(f"[Nó {self.id_no}] Divergência de Checksum para a query: {sql}")
            return
            
        try:
            print(f"[Nó {self.id_no}] Executando query replicada do Nó {msg['origin']}")
            cursor = self.conexao_bd.cursor()
            cursor.execute(sql)
        except Error as e:
            print(f"[Nó {self.id_no}] Erro na replicação: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python node.py <id_do_no>")
        sys.exit(1)
    
    id_no_args = int(sys.argv[1])

    # Redirecionar stdout e stderr para um arquivo de log
    dir_logs = "logs"
    if not os.path.exists(dir_logs):
        os.makedirs(dir_logs)
    arquivo_log = os.path.join(dir_logs, f"node{id_no_args}.log")
    
    # Abrir arquivo de log com buffer de linha (buffering=1)
    fp_log = open(arquivo_log, 'w', buffering=1)
    sys.stdout = fp_log
    sys.stderr = fp_log

    no = No(id_no_args)
    
    print(f"Nó {id_no_args} iniciado. Pressione Ctrl+C para parar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        no.parar()
        print("Nó parando...")