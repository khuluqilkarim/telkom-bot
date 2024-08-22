from helper.connection import create_connection, close_connection
from mysql.connector import Error
from datetime import datetime
import json

def get_user_by_id(user_id):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        print(f"\033[93mDEBUG \033[96mget_user_by_id\033[0m func :: \033[92msuccess\033[0m")
        return user
    except Error as e:
        print(f"\033[91mError \033[96mget_user_by_id\033[0m func :: {e}")
        return None
    finally:
        close_connection(connection)

def getLogBook(randID, user_id):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM logbook_submissions WHERE user_id = %s AND id = %s AND is_approve = 0", (user_id, randID))
        user = cursor.fetchone()
        if user is not None:
            print(f"\033[93mDEBUG \033[96mgetLogBook\033[0m func :: \033[92msuccess\033[0m")
        else:
            print(f"\033[93mDEBUG \033[96mgetLogBook\033[0m func :: \033[93mno data found\033[0m")
            
        return user
    except Error as e:
        print(f"\033[91mError \033[96mgetLogBook\033[0m func :: {e}")
        return None
    finally:
        close_connection(connection)

def isKeysOdcAvailable(odc_name='', data_id=''):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM odc_info WHERE Nama = %s OR Data_ID = %s", (odc_name,data_id))
        user = cursor.fetchone()
        print(f"\033[93mDEBUG \033[96misKeysOdcAvailable\033[0m func :: \033[92msuccess\033[0m")
        return user
    except Error as e:
        print(f"\033[91mError \033[96misKeysOdcAvailable\033[0m func :: {e}")
        return None
    finally:
        close_connection(connection)

def register_user(user_id, username):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO users (user_id, username, is_registered) VALUES (%s, %s, %s)",
                       (user_id, username, False))
        connection.commit()
        print(f"\033[93mDEBUG \033[96mregister_user\033[0m func :: \033[92msuccess\033[0m")

    except Error as e:
        print(f"\033[91mError \033[96mregister_user\033[0m func :: {e}")
    finally:
        close_connection(connection)

def update_registration_status(user_id, status):
    print(f"status : {status}\nUser id : {user_id}")
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE users SET is_registered = %s WHERE user_id = %s", (status, user_id))
        connection.commit()
        print(f"\033[93mDEBUG \033[96mupdate_registration_status\033[0m func :: \033[92msuccess\033[0m")
    except Error as e:
        print(f"\033[91mError \033[96mupdate_registration_status\033[0m func :: {e}")
    finally:
        close_connection(connection)

def borrow_key(user_id, key_name, key_id, randID):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE odc_info SET is_key_available = 0 WHERE Nama = %s", (key_name,))
        cursor.execute("INSERT INTO borrowed_keys (id, key_id, user_id, time_borrowed, keys_returned, is_return) VALUES (%s, %s, %s, current_timestamp(), NULL, '0')", (randID,key_id, user_id))
        cursor.execute("INSERT INTO logbook_submissions (id, user_id, Nama_ODC, is_approve) VALUES (%s, %s, %s, 0)",(randID, user_id, key_name))

        connection.commit()
        print(f"\033[93mDEBUG \033[96mborrow_key\033[0m func :: User {user_id} borrowed key {key_name} successfully")
        return True
    except Error as e:
        print(f"\033[91mError \033[96mborrow_key\033[0m func :: {e}")
        return False
    finally:
        close_connection(connection)

def return_key(user_id, key_name):
    now = datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE odc_info SET is_key_available = 1 WHERE Nama = %s", (key_name,))
        cursor.execute("UPDATE logbook_submissions SET is_approve = 1 WHERE user_id = %s AND Nama_ODC = %s",(user_id,key_name))
        connection.commit()
        print(f"\033[93mDEBUG \033[96mreturn_key\033[0m func :: \033[92msuccess\033[0m")
        return True
    except Error as e:
        print(f"\033[91mError \033[96mreturn_key\033[0m func :: {e}")
        return False
    finally:
        close_connection(connection)

def finishReturning(user_id, key_id, randID):
    now = datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE borrowed_keys SET keys_returned = %s, is_return = 1 WHERE user_id  = %s AND key_id = %s AND id = %s",(time_format, user_id, key_id, randID))
        connection.commit()
        print(f"\033[93mDEBUG \033[96mreturn_key\033[0m func :: \033[92msuccess\033[0m")
        return True
    except Error as e:
        print(f"\033[91mError \033[96mreturn_key\033[0m func :: {e}")
        return False
    finally:
        close_connection(connection)

def insert_logbook(user_id, key_name, message, randID):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("INSERT INTO logbook_submissions (id, user_id, message, timestamp, Nama_ODC, is_approve) VALUES (%s, %s, %s, current_timestamp(), %s, 0)",(randID, user_id, message, key_name))
        connection.commit()
        print(f"\033[93mDEBUG \033[96minsert_logbook\033[0m func :: \033[92msuccessfull\033[0m")
        return True
    except Error as e:
        print(f"\033[91mError \033[96minsert_logbook\033[0m func :: {e}")
        return False
    finally:
        close_connection(connection)

def Update_logbook(message, randID):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE logbook_submissions SET message = %s, timestamp = current_timestamp() WHERE id = %s",( message, randID))
        connection.commit()
        print(f"\033[93mDEBUG \033[96mUpdate_logbook\033[0m func :: \033[92msuccessfull\033[0m")
        return True
    except Error as e:
        print(f"\033[91mError \033[96mUpdate_logbook\033[0m func :: {e}")
        return False
    finally:
        close_connection(connection)

def isUserBorrowed(user_id):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM borrowed_keys WHERE user_id = %s and is_return = 0", (user_id,))
        users = cursor.fetchall()
        if users:
            borrowed_list = []
            for user in users:
                user_dict = {
                    'id': user[0], 
                    'key_id': user[1],
                    'user_id': user[2],
                    'time_borrowed': user[3].strftime('%Y-%m-%d %H:%M:%S') if isinstance(user[3], datetime) else user[3],
                    'keys_returned': user[4],
                    'is_returned': user[5],
                }
                borrowed_list.append(user_dict)

            user_json = json.dumps(borrowed_list)
            print(f"\033[93mDEBUG \033[96misUserBorrowed\033[0m func :: \033[92msuccess\033[0m, found {len(borrowed_list)} records")
            return user_json
        else:
            print(f"\033[93mDEBUG \033[96misUserBorrowed\033[0m func :: \033[93mno data found\033[0m")
            return None
    except Error as e:
        print(f"\033[91mError \033[96misUserBorrowed\033[0m func :: {e}")
        return None
    finally:
        close_connection(connection)
