import mysql.connector

config_bd = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'root',
    'database': 'bd-dist',
    'port': 3307,
    'connect_timeout': 5
}

print("Testing MySQL connection...")
try:
    conn = mysql.connector.connect(**config_bd)
    if conn.is_connected():
        print("Connected!")
        conn.autocommit = True
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchall()
        print(f"Result: {result}")
        conn.close()
        print("Success!")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
