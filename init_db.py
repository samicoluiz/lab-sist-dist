import mysql.connector
import json

def inicializar():
    try:
        with open('config.json', 'r') as f:
            nos = json.load(f)['nodes']
    except FileNotFoundError:
        print("Erro: 'config.json' não encontrado. Execute 'iniciar_ambiente' ou gere-o manualmente.")
        return
    
    for n in nos:
        conn = None
        try:
            conn = mysql.connector.connect(
                host=n['ip'],
                user='root',
                password='root',
                database='bd-dist',
                port=n['db_port']
            )
            # Usando 'with' para garantir o fechamento do cursor
            with conn.cursor() as cursor:
                cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))")
            
            print(f"Banco de dados do Nó {n['id']} inicializado.")
            
        except Exception as e:
            print(f"Erro ao inicializar o Nó {n['id']}: {e}")
        finally:
            if conn and conn.is_connected():
                conn.close()

if __name__ == "__main__":
    inicializar()