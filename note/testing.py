from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, filters, MessageHandler
from telegram import InputMediaPhoto
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import json

user_submissions = {}

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
        print(f"\033[93mDEBUG \033[96mcreate_connection\033[0m func :: \033[92msuccess\033[0m")

    except Error as e:
        print(f"\033[91mError \033[96mcreate_connection\033[0m func :: {e}")
    return connection

def close_connection(connection):
    print(f"\033[93mDEBUG \033[96mclose_connection\033[0m func :: \033[92msuccess\033[0m")

    if connection.is_connected():
        connection.close()

def isUserBorrowed(user_id):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM borrowed_keys WHERE user_id = %s and is_return = 0", (user_id,))
        user = cursor.fetchone()
        if user:
            user_dict = {
                'id': user[0], 
                'key_id': user[1],
                'user_id': user[2],
                'time_borrowed': user[3].strftime('%Y-%m-%d %H:%M:%S') if isinstance(user[3], datetime) else user[3],
                'keys_returned': user[4],
                'is_returned': user[5],
            }
            user_json = json.dumps(user_dict)
            print(f"\033[93mDEBUG \033[96misUserBorrowed\033[0m func :: \033[92msuccess\033[0m")
            return user_json
        else:
            print(f"\033[93mDEBUG \033[96misUserBorrowed\033[0m func :: \033[93mno data found\033[0m")
            return None
    except Error as e:
        print(f"\033[91mError \033[96misUserBorrowed\033[0m func :: {e}")
        return None
    finally:
        close_connection(connection)

print(isUserBorrowed(5721823426))