import pandas as pd
import mysql.connector
from mysql.connector import Error

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',        # Ganti dengan host database Anda
            database='odc_keys_witel_jember', # Ganti dengan nama database Anda
            user='root',         # Ganti dengan username database Anda
            password=''  # Ganti dengan password database Anda
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def close_connection(connection):
    if connection.is_connected():
        connection.close()

def insert_data_from_excel(file_path):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
     
    cursor = connection.cursor()
    try:
        # Baca data dari file Excel
        df = pd.read_excel(file_path)

        # SQL query to insert data
        insert_query = """
        INSERT INTO odc_info (Data_ID, Regional, Witel, Datel, STO, Nama, Deskripsi, Latitude, Longitude, Status_Polygon, Timestamp, Status_Object, ODC_Status, is_key_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'True')
        """
        
        # Convert dataframe to list of tuples
        data = df.values.tolist()

        # Execute the insert query with provided data
        cursor.executemany(insert_query, data)
        connection.commit()
        print("Data inserted successfully")
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        close_connection(connection)

# Path to your Excel file
file_path = 'ODC.xlsx'

# Call the function to insert data
insert_data_from_excel(file_path)
