import mysql.connector
from mysql.connector import Error

db_config = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'odc_keys_witel_jember'
}

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
    except Error as e:
        print(f"\033[91mError \033[96mcreate_connection\033[0m func :: {e}")
    return connection

def close_connection(connection):
    if connection.is_connected():
        connection.close()