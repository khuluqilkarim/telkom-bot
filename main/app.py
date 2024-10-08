from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, filters, MessageHandler
from telegram import InputMediaPhoto
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
import json
import random
import string

user_submissions = {}

db_config = {
    'user': 'ama',
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
        cursor.execute("SELECT * FROM logbook_submissions WHERE user_id = %s AND id = %s", (user_id, randID))
        user = cursor.fetchone()
        print(f"\033[93mDEBUG \033[96mgetLogBook\033[0m func :: \033[92msuccess\033[0m")
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
        print(f"\033[93mDEBUG \033[96minsert_logbook\033[0m func :: \033[92msuccessfull\033[0m")
        return True
    except Error as e:
        print(f"\033[91mError \033[96minsert_logbook\033[0m func :: {e}")
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

def createFolder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        return False
    
    print(f"\033[93mDEBUG \033[96mcreateFolder\033[0m func :: \033[92msuccess\033[0m")

async def downloadFile(file,file_name):
    try: 
        await file.download_to_drive(file_name)
        print(f"\033[93mDEBUG \033[96mdownloadFile\033[0m func :: \033[92msuccess\033[0m")
    except Error as e:
        print(f"\033[91mError \033[96mdownloadFile\033[0m func :: {e}")


def generateID(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def register_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"regist_approve_{user_id}")],
            [InlineKeyboardButton("Reject", callback_data=f"regist_reject_{user_id}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id='5168019992', text=f"New users come and ask for a registration request:\nUser: @{query.from_user.username}\nPlease approve or reject this request.", reply_markup=reply_markup)
    print(f"\033[93mDEBUG \033[96mregister_callback\033[0m func :: \033[92msuccess\033[0m")

async def handle_registration(update: Update, context: CallbackContext):
    _, validasi, id_register  = update.callback_query.data.split("_")
    
    if validasi == "approve":
        update_registration_status(id_register, True)
        await context.bot.send_message(chat_id=id_register, text=f"Anda telah berhasil menjadi user")
    else:
        await context.bot.send_message(chat_id=id_register, text=f"Permintaan anda ditolak")
    
    print(f"\033[93mDEBUG \033[96mhandle_registration\033[0m func :: \033[92msuccess\033[0m")

async def notify_callback(update: Update , context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"alert_notify_approve_{user_id}")],
            [InlineKeyboardButton("Reject", callback_data=f"alert_notify_reject_{user_id}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id='5168019992', text=f"new users need to be approved for teh access:\nUser: @{query.from_user.username}\nPlease approve or reject this request.", reply_markup=reply_markup)
    print(f"\033[93mDEBUG \033[96mnotify_callback\033[0m func :: \033[92msuccess\033[0m")

async def handle_notify(update: Update, context: CallbackContext):
    _, __, validasi , id_register = update.callback_query.data.split("_")

    if validasi == "approve":
        update_registration_status(id_register, True)
        await context.bot.send_message(chat_id=id_register, text=f"Anda telah berhasil menjadi user")
    else:
        await context.bot.send_message(chat_id=id_register, text=f"Permintaan anda ditolak")
    
    print(f"\033[93mDEBUG \033[96mhandle_notify\033[0m func :: \033[92msuccess\033[0m")

async def request_key_name(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text("Untuk melanjutkan proses peminjaman, silakan masukkan nama kunci yang ingin Anda pinjam :")
    print(f"\033[93mDEBUG \033[96mrequest_key_name\033[0m func :: \033[92msuccess\033[0m")

async def forward_chat_request(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    key_name = update.message.text

    data = get_user_by_id(user_id)
    print(data)

    if data is None:
        await context.bot.send_message(chat_id=user_id, text=f"Anda belum terdaftar, lakukan /start dan mendaftar")
        return
    elif update.message.text.split('-')[0] == 'ODC':
        validasi = isKeysOdcAvailable(key_name)
        randID = user_submissions[user_id]["randID"]
        if validasi is not None and validasi['is_key_available'] == 1:

            keyboard = [
                [InlineKeyboardButton("Approve", callback_data=f"borrow_approve_{user_id}_{key_name}_{randID}")],
                [InlineKeyboardButton("Reject", callback_data=f"borrow_reject_{user_id}_{key_name}_{randID}")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=user_id, text=f"Permintaan peminjaman kunci {key_name} telah diajukan.")
            await context.bot.send_message(chat_id='5168019992', text=f"Request peminjaman kunci:\nUser: @{username}\nKunci: {key_name}\nPlease approve or reject this request.", reply_markup=reply_markup)
        if validasi is not None and validasi['is_key_available'] == 0:
            await context.bot.send_message(chat_id=user_id, text=f"Permintaan peminjaman kunci {key_name} telah digunakan orang lain")
        if validasi is None: 
            await context.bot.send_message(chat_id=user_id, text=f"Kunci dengan code {key_name} tidak ditemukan")
    else:
        print(update)
    
    print(f"\033[93mDEBUG \033[96mforward_chat_request\033[0m func :: \033[92msuccess\033[0m")

async def handle_borrow_approval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    _, action, user_id, key_name, randID = query.data.split("_")
    dataODC = isKeysOdcAvailable(key_name)

    if action == "approve":
        borrow_key(user_id, key_name, dataODC['Data_ID'], randID)
        await context.bot.send_message(chat_id=user_id, text=f"*Keterangan*:\n\nStatus Peminjaman: *Approve*\nODC Name: *{key_name}*\nLocation: [Google Maps](https://www.google.com/maps?q={dataODC['Latitude']},{dataODC['Longitude']})\n\nSilakan ambil kunci Anda di lokasi yang telah ditentukan oleh Team Leader Region.",parse_mode='markdown')
    else:
        await context.bot.send_message(chat_id=user_id, text=f"Permintaan peminjaman kunci {key_name} Anda telah ditolak.")
    
    print(f"\033[93mDEBUG \033[96mhandle_borrow_approval\033[0m func :: \033[92msuccess\033[0m")

async def returnKeys_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keyboard = [
            [InlineKeyboardButton("Pengembalian Kunci", callback_data=f"keys_returning")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("", reply_markup=reply_markup) 
    print(f"\033[93mDEBUG \033[96mreturnKeys_callback\033[0m func :: \033[92msuccess\033[0m")

async def handle_returnKeyLogbook(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    _, key_name = update.callback_query.data.split('_')

    isUserborrow_json = isUserBorrowed(user_id)
    isUserborrow = json.loads(isUserborrow_json)

    data = isKeysOdcAvailable(data_id=int(isUserborrow['key_id']))

    keyboard = [
            [InlineKeyboardButton("Setuju dan lengkapi", callback_data=f"Logbook_{key_name}")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text=f"*Tatacara pengembalian* :\n\n1. Informasikan kegiatan yang anda lakukan di {data['Nama']} :\n2. Upload Foto Kondisi ODC sebelum pekerjaan (*tampak dalam*)\n3. Upload Foto Kondisi ODC setelah pekerjaan (*tampak dalam*)\n4. Upload Foto Kondisi ODC telah tertutup dan terkunci kembali (*tampak depan*)", parse_mode='markdown', reply_markup=reply_markup)
    print(f"\033[93mDEBUG \033[96mhandle_returnKeyLogbook\033[0m func :: \033[92msuccess\033[0m ")

async def logbook(update: Update, context: CallbackContext):
    _, key_name = update.callback_query.data.split('_')
    await update.callback_query.message.reply_text(f"Kirim logbook pada peminjaman kunci {key_name} anda :")
    print(f"\033[93mDEBUG \033[96mlogbook\033[0m func :: \033[92msuccess\033[0m")

async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    message = update.message.caption
    photo_file = await update.message.photo[-1].get_file()
    if message is not None:
        user_submissions[user_id]["message"] = message

    if user_id in user_submissions:
        if len(user_submissions[user_id]["photos"]) < 3:
            user_submissions[user_id]["file_photos"].append(photo_file)
            user_submissions[user_id]["photos"].append(update.message.photo[-1].file_id)
            if len(user_submissions[user_id]["photos"]) == 3:
                await update.message.reply_text("Terima kasih telah melengkapi logbook ini. Saat ini, logbook sedang dalam proses evaluasi. Mohon tunggu hingga Team Leader memberikan persetujuan sebelum melanjutkan pengembalian")
                await forward_to_team_leader(update, context, user_id)
        else:
            await update.message.reply_text("Tidak perlu mengirimkan lebih dari 3 foto, data anda sedang di review oleh Team ")
    else:
        await update.message.reply_text("Please start by sending the /start command.")
    
    print(f"\033[93mDEBUG \033[96mhandle_photo\033[0m func :: \033[92msuccess\033[0m")

async def forward_to_team_leader(update: Update, context: CallbackContext, user_id: int):
    submission = user_submissions.get(user_id)
    username = get_user_by_id(user_id)['username']

    isUserborrow_json = isUserBorrowed(int(user_id))
    isUserborrow = json.loads(isUserborrow_json)
    data_ODC = isKeysOdcAvailable(data_id=isUserborrow['key_id'])
    randID = user_submissions[user_id]["randID"]

    keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"keyReturn_approve_{user_id}_{data_ODC['Nama']}_{randID}")],
            [InlineKeyboardButton("Reject", callback_data=f"keyReturn_reject_{user_id}_{data_ODC['Nama']}_{randID}")]
            ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    now = datetime.now()

    if submission:
        photos = submission["photos"]
        message = submission["message"]

        iskeyreturn = getLogBook(user_submissions[user_id]['randID'],user_id)

        if iskeyreturn is not None:
            Update_logbook(message,randID)

        insert_logbook(user_id,data_ODC['Nama'],message, randID)
        
        text = f"*Logbook* :\nKey : *{data_ODC['Nama']}*\nWaktu : *{now.strftime("%Y-%m-%d %H:%M:%S")}*\n\nPesan :\n{message}"

        try:
            media_group = [InputMediaPhoto(media=photo_id) for photo_id in photos]
            await context.bot.send_media_group(chat_id='5168019992', media=media_group, caption=text, parse_mode='markdown')
            await context.bot.send_message(chat_id='5168019992',text=f"Request pengembalian kunci:\nUser: @{username}\nKey : {data_ODC['Nama']}",reply_markup=reply_markup)

        except Exception as e:
            print(f"\033[91mError \033[96mforward_to_team_leader\033[0m func :: {e}")
    else:
        print("No submission found for user:", user_id)

    print(f"\033[93mDEBUG \033[96mforward_to_team_leader\033[0m func :: \033[92msuccess\033[0m")
    
async def handle_returnKey_approval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, action, user_id, key_name, randID = query.data.split("_")
    dataODC = isKeysOdcAvailable(key_name)

    now = datetime.now()
    folder = now.strftime("%Y-%m-%d")
    file_time = now.strftime("%H%M%S")
    data_user = get_user_by_id(user_id)
    n = 0

    folder_format = f"Logbook/{folder}/{data_user['username']}"

    if action == "approve":
        createFolder(folder_format)
        return_key(user_id,key_name)

        for data in user_submissions[int(user_id)]['file_photos']:
            n += 1
            file_name = f"{folder_format}/{data_user['username']}_{file_time}_{key_name}_{n}.jpg"
            await downloadFile(data,file_name)

        keyboard = [
            [InlineKeyboardButton("Pengembalian selesai", callback_data=f"USRkeys_{user_id}_{key_name}_{randID}")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text=f"Logbook disetujui. Harap kembalikan kunci {dataODC['Nama']} segera.",reply_markup=reply_markup)

        user_submissions[int(user_id)]['file_photos'] = []
        user_submissions[int(user_id)]['photos'] = []
        user_submissions[int(user_id)]['message'] = None
        print(user_submissions[int(user_id)])
    else:
        await context.bot.send_message(chat_id=user_id, text=f"Logbook ditolak. Harap isi kembali.")
        user_submissions[int(user_id)]['file_photos'] = []
        user_submissions[int(user_id)]['photos'] = []
        user_submissions[int(user_id)]['message'] = None
        print(user_submissions[int(user_id)])
        
        print(f"\033[93mDEBUG \033[96muser_submissions\033[0m data :: \033[92m{user_submissions[int(user_id)]}\033[0m")

    print(f"\033[93mDEBUG \033[96mhandle_returnKey_approval\033[0m func :: \033[92msuccess\033[0m")

async def handle_finishReturnKeys_approval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, user_id, key_name, randID = query.data.split("_")
    data_user = get_user_by_id(user_id)

    keyboard = [
            [InlineKeyboardButton("Sudah", callback_data=f"TLkeys_approve_{user_id}_{key_name}_{randID}")],
            [InlineKeyboardButton("Belum", callback_data=f"TLkeys_reject_{user_id}_{key_name}_{randID}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id='5168019992', text=f"Apakah user ini @{data_user['username']} telah mengembalikan kunci {key_name}?", reply_markup=reply_markup)
    
async def finishReturnKeys_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, action, user_id, key_name, randID = query.data.split("_")

    isUserborrow_json = isUserBorrowed(int(user_id))
    isUserborrow = json.loads(isUserborrow_json)
    data_ODC = isKeysOdcAvailable(data_id=isUserborrow['key_id'])

    if action == 'approve':
        del user_submissions[int(user_id)]
        finishReturning(user_id,data_ODC['Data_ID'], randID)
        await context.bot.send_message(chat_id=user_id, text=f"Terimakasih telah mengembalikan.")
    elif action == 'reject':
        await returningKeysButton(user_id, key_name, context, randID)
        
async def returningKeysButton(user_id, key_name, context, randID):
    dataODC = isKeysOdcAvailable(key_name)
    keyboard = [
            [InlineKeyboardButton("Pengembalian selesai", callback_data=f"USRkeys_{user_id}_{key_name}_{randID}")]
            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text=f"Harap kembalikan kunci {dataODC['Nama']} segera.",reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)
    print(f"\033[93mDEBUG\033[0m : Sesi Approval :: {query.data}")

    if query.data == 'register':
        await register_callback(update, context)
    elif query.data.split('_')[0] == 'regist':
        await handle_registration(update, context)
    elif query.data == 'notify':
        await notify_callback(update, context)
    elif query.data.split('_')[0] == 'alert':
        await handle_notify(update, context)
    elif query.data == 'keys_borrowed':
        await request_key_name(update,context)
    elif query.data.startswith('borrow'):
        await handle_borrow_approval(update, context)
    elif query.data.split('_')[0] == 'returnKeys':
        await handle_returnKeyLogbook(update, context)
    elif query.data.split('_')[0] == 'Logbook':
        await logbook(update, context)
    elif query.data.split('_')[0] == 'keyReturn':
        await handle_returnKey_approval(update, context)
    elif query.data.split('_')[0] == 'USRkeys':
        await handle_finishReturnKeys_approval(update, context)
    elif query.data.split('_')[0] == 'TLkeys':
        await finishReturnKeys_callback(update, context)

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    
    if user_id not in user_submissions:
        user_submissions[user_id] = {
            "photos": [],
            "file_photos": [],
            "message": None,
            "randID": None
        }
    print(f"\n\033[91mDEBUG \033[96muser_submissions\033[0m data is None :: \033[93m{user_submissions[user_id]}\033[0m")

    if user_submissions[user_id]["randID"] is None:
        user_submissions[user_id]["randID"] = generateID()

    print(f"\033[93mDEBUG \033[96muser_submissions\033[0m data Created :: \033[92m{user_submissions[user_id]}\033[0m")

    data = get_user_by_id(user_id)
    isUserborrow_json = isUserBorrowed(int(user_id))
    iskeyreturn = getLogBook(user_submissions[user_id]['randID'], user_id)

    print(f"iskeyreturn :: {iskeyreturn}")

    isUserborrow = None
    if isUserborrow_json is not None:
        try:
            isUserborrow = json.loads(isUserborrow_json)
        except json.JSONDecodeError as e:
            print(f"\033[91mError \033[96misUserBorrowed\033[0m func :: JSON decoding error: {e}")

    print(f"isUserborrow :: {isUserborrow}")

    if iskeyreturn is not None and iskeyreturn['is_approve'] == 0:
        if isUserborrow is not None:
            data_ODC = isKeysOdcAvailable(data_id=int(isUserborrow['key_id']))
            print(data_ODC)
            keyboard = [
                [InlineKeyboardButton(f"Kembalikan Kunci {data_ODC['Nama']}", callback_data=f"returnKeys_{data_ODC['Nama']}")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Anda meminjam kunci {data_ODC['Nama']}. Harap isi logbook dan kembalikan kunci setelah tugas selesai.", 
                reply_markup=reply_markup
            )
        else:
            print("isUserborrow is None, cannot retrieve key data.")
    
    elif isUserborrow is not None and isUserborrow['is_returned'] == 0:
        data_ODC = isKeysOdcAvailable(data_id=int(isUserborrow['key_id']))
        await returningKeysButton(user_id, data_ODC['Nama'], context, user_submissions[user_id]['randID'])
    
    elif data is not None:
        if data['is_registered'] == 1:
            keyboard = [
                [InlineKeyboardButton("Ketersedian Kunci", callback_data='show_keys')],
                [InlineKeyboardButton("Peminjaman Kunci", callback_data='keys_borrowed')],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Selamat datang di layanan manajemen kunci kami! Untuk memulai, silakan pilih salah satu opsi dari menu di bawah ini sesuai dengan kebutuhan Anda.", 
                reply_markup=reply_markup
            )
        elif data['is_registered'] == 0:
            keyboard = [
                [InlineKeyboardButton("Notify Team Lead", callback_data='notify')],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Permintaan Anda sebagai pengguna belum disetujui oleh Team Leader.", 
                reply_markup=reply_markup
            )
    else:
        register_user(user_id, username)
        keyboard = [
            [InlineKeyboardButton("Register", callback_data='register')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Belum mendaftar? Tekan tombol di bawah untuk mendaftar.", 
            reply_markup=reply_markup
        )


def main():
    application = Application.builder().token("7367838125:AAGFZMDYE0le6VjZtlqzzLiECjWCT12rDFA").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_chat_request))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()

# note : 

# - limit peminjaman kunci :
#     - dikurangi jika meminjam (done)
#     - ditambah ketika di tolak
#     - 