import mysql.connector
import json

def init():
    with open('config.json', 'r') as f:
        nodes = json.load(f)['nodes']
    
    for n in nodes:
        try:
            conn = mysql.connector.connect(
                host=n['ip'],
                user='root',
                password='root',
                database='bd-dist',
                port=n['db_port']
            )
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255))")
            print(f"Initialized Node {n['id']} database.")
            conn.close()
        except Exception as e:
            print(f"Error initializing Node {n['id']}: {e}")

if __name__ == "__main__":
    init()
