import socket
import threading
import json
import time
import hashlib
import mysql.connector
from mysql.connector import Error
import sys

class Node:
    def __init__(self, node_id, config_path='config.json'):
        self.node_id = node_id
        self.load_config(config_path)
        self.me = self.nodes_info[node_id]
        self.other_nodes = [n for n in self.nodes_info if n['id'] != node_id]
        
        self.db_config = {
            'host': self.me['ip'],
            'user': 'root',
            'password': 'root',
            'database': 'bd-dist',
            'port': self.me['db_port']
        }
        
        self.coordinator_id = None
        self.alive_nodes = {self.node_id: time.time()}
        self.is_running = True
        
        # Lock for thread-safe operations on state
        self.lock = threading.Lock()
        
        # Connect to MySQL
        self.db_conn = self.connect_db()
        
        # Start server thread
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Start heartbeat thread
        self.hb_thread = threading.Thread(target=self.send_heartbeat)
        self.hb_thread.daemon = True
        self.hb_thread.start()
        
        # Start monitor thread to check node health and trigger election
        self.monitor_thread = threading.Thread(target=self.monitor_nodes)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Initial election
        self.start_election()

    def load_config(self, path):
        with open(path, 'r') as f:
            self.nodes_info = json.load(f)['nodes']

    def connect_db(self):
        while self.is_running:
            try:
                conn = mysql.connector.connect(**self.db_config)
                if conn.is_connected():
                    print(f"[Node {self.node_id}] Connected to MySQL at port {self.me['db_port']}")
                    conn.autocommit = True
                    return conn
            except Error as e:
                print(f"[Node {self.node_id}] MySQL Connection Error: {e}. Retrying...")
                time.sleep(5)
        return None

    def calculate_checksum(self, data):
        return hashlib.md5(data.encode()).hexdigest()

    def send_msg(self, target_node, msg):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((target_node['ip'], target_node['port']))
                s.sendall(json.dumps(msg).encode())
        except Exception:
            # Node might be down
            pass

    def broadcast(self, msg):
        for node in self.other_nodes:
            self.send_msg(node, msg)

    def run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.me['ip'], self.me['port']))
        self.server_socket.listen(5)
        print(f"[Node {self.node_id}] Listening on {self.me['ip']}:{self.me['port']}")
        
        self.server_socket.settimeout(1.0)
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn,)).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    print(f"[Node {self.node_id}] Server error: {e}")

    def stop(self):
        self.is_running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()
        if self.db_conn:
            self.db_conn.close()
        print(f"[Node {self.node_id}] Stopped.")

    def handle_client(self, conn):
        with conn:
            data = conn.recv(4096)
            if not data:
                return
            msg = json.loads(data.decode())
            self.process_message(msg)

    def process_message(self, msg):
        m_type = msg.get('type')
        
        if m_type == 'HEARTBEAT':
            with self.lock:
                self.alive_nodes[msg['id']] = time.time()
                
        elif m_type == 'ELECTION':
            if msg['id'] < self.node_id:
                # Answer OK and start own election
                sender = next(n for n in self.nodes_info if n['id'] == msg['id'])
                self.send_msg(sender, {'type': 'ELECTION_OK', 'id': self.node_id})
                self.start_election()
                
        elif m_type == 'COORDINATOR':
            with self.lock:
                self.coordinator_id = msg['id']
                print(f"[Node {self.node_id}] New Coordinator: {self.coordinator_id}")
                
        elif m_type == 'REPLICATE':
            self.execute_replicated_query(msg)

    def send_heartbeat(self):
        while self.is_running:
            self.broadcast({'type': 'HEARTBEAT', 'id': self.node_id})
            time.sleep(2)

    def monitor_nodes(self):
        while self.is_running:
            time.sleep(5)
            now = time.time()
            with self.lock:
                dead_nodes = [nid for nid, last_seen in self.alive_nodes.items() 
                              if now - last_seen > 10 and nid != self.node_id]
                for nid in dead_nodes:
                    print(f"[Node {self.node_id}] Node {nid} is down")
                    del self.alive_nodes[nid]
                    if self.coordinator_id == nid:
                        self.coordinator_id = None
                        self.start_election()

    def start_election(self):
        print(f"[Node {self.node_id}] Starting election...")
        higher_nodes = [n for n in self.other_nodes if n['id'] > self.node_id]
        if not higher_nodes:
            # I am the highest, I am the coordinator
            self.coordinator_id = self.node_id
            self.broadcast({'type': 'COORDINATOR', 'id': self.node_id})
            print(f"[Node {self.node_id}] I am the coordinator")
        else:
            for n in higher_nodes:
                self.send_msg(n, {'type': 'ELECTION', 'id': self.node_id})
            
            # Wait for OK
            time.sleep(2.0)
            
            # If after waiting, I still don't know who the coordinator is, 
            # and I haven't received a 'COORDINATOR' message from someone bigger,
            # it means the bigger nodes are dead. I take over.
            if self.coordinator_id is None:
                print(f"[Node {self.node_id}] No higher node responded. I am taking over!")
                self.coordinator_id = self.node_id
                self.broadcast({'type': 'COORDINATOR', 'id': self.node_id})

    def execute_query(self, sql):
        # Determine if it's WRITE or READ
        is_write = any(keyword in sql.upper() for keyword in ["INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER"])
        
        checksum = self.calculate_checksum(sql)
        print(f"[Node {self.node_id}] RECEIVED QUERY: {sql}")
        
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute(sql)
            
            result = None
            if not is_write:
                result = cursor.fetchall()
                print(f"[Node {self.node_id}] READ operation executed locally. Rows returned: {len(result)}")
            
            if is_write:
                # Replicate
                print(f"[Node {self.node_id}] WRITE operation. Transmitting content for replication...")
                print(f"[Node {self.node_id}] Checksum: {checksum}")
                self.broadcast({
                    'type': 'REPLICATE',
                    'sql': sql,
                    'checksum': checksum,
                    'origin': self.node_id
                })
                print(f"[Node {self.node_id}] Replication broadcast finished.")
            
            return {"status": "success", "node": self.node_id, "data": result}
        except Error as e:
            print(f"[Node {self.node_id}] SQL Error: {e}")
            return {"status": "error", "node": self.node_id, "message": str(e)}

    def execute_replicated_query(self, msg):
        sql = msg['sql']
        received_checksum = msg['checksum']
        
        # Verify integrity
        if self.calculate_checksum(sql) != received_checksum:
            print(f"[Node {self.node_id}] Checksum mismatch for query: {sql}")
            return
            
        try:
            print(f"[Node {self.node_id}] Executing replicated query from Node {msg['origin']}")
            cursor = self.db_conn.cursor()
            cursor.execute(sql)
        except Error as e:
            print(f"[Node {self.node_id}] Error in replication: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python node.py <node_id>")
        sys.exit(1)
    
    node_id = int(sys.argv[1])
    node = Node(node_id)
    
    # Keep the main thread alive to handle client queries via another socket 
    # OR we can just use the same server socket and add a 'CLIENT_QUERY' type.
    
    # Adding CLIENT_QUERY handling to process_message
    def extended_process_message(self, msg, conn=None):
        m_type = msg.get('type')
        if m_type == 'CLIENT_QUERY':
            response = self.execute_query(msg['sql'])
            if conn:
                conn.sendall(json.dumps(response).encode())
        else:
            self.process_message(msg)

    # Patching the handle_client to support response
    def patched_handle_client(self, conn):
        try:
            data = conn.recv(8192)
            if not data: return
            msg = json.loads(data.decode())
            
            if msg.get('type') == 'CLIENT_QUERY':
                # Load balancing: if I'm busy (simulated) or just round-robin
                # For this lab, let's just execute locally or if it's a read, 
                # maybe give it to someone else if we want load balancing.
                response = self.execute_query(msg['sql'])
                conn.sendall(json.dumps(response).encode())
            elif msg.get('type') == 'GET_COORDINATOR':
                response = {'status': 'success', 'coordinator_id': self.coordinator_id}
                conn.sendall(json.dumps(response).encode())
            else:
                self.process_message(msg)
        except Exception as e:
            print(f"Error handling message: {e}")
        finally:
            conn.close()

    Node.handle_client = patched_handle_client
    
    print(f"Node {node_id} started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        node.is_running = False
        print("Node stopping...")
