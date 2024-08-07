from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, filters, MessageHandler
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
        print(f"Error: {e}")
    return connection

def close_connection(connection):
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
        return user
    except Error as e:
        print(f"Error: {e}")
        return None
    finally:
        close_connection(connection)

def isKeysOdcAvailable(odc_name='',data_id=''):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return None
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM odc_info WHERE Nama = %s OR Data_ID = %s", (odc_name,data_id))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error: {e}")
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
        print(f"User {username} registered successfully")
    except Error as e:
        print(f"Error: {e}")
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
        print(f"User {user_id} registration status updated to {status}")
    except Error as e:
        print(f"Error: {e}")
    finally:
        close_connection(connection)

def borrow_key(user_id, key_name, key_id):
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return False
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE odc_info SET is_key_available = 0 WHERE Nama = %s", (key_name,))
        cursor.execute("INSERT INTO borrowed_keys (id, key_id, user_id, time_borrowed, keys_returned, is_return) VALUES (NULL, %s, %s, current_timestamp(), NULL, '0')", (key_id, user_id))
        connection.commit()
        print(f"User {user_id} borrowed key {key_name} successfully")
        return True
    except Error as e:
        print(f"Error: {e}")
        return False
    finally:
        close_connection(connection)

def isUserBorrowed(user_id):
    print('isUserBorrowed section')
    connection = create_connection()
    if connection is None:
        print("Failed to create database connection.")
        return
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM borrowed_keys WHERE user_id = %s and is_return = 0", (user_id,))
        user = cursor.fetchone()
        return user
    except Error as e:
        print(f"Error: {e}")
        return None
    finally:
        close_connection(connection)

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    data = get_user_by_id(user_id)
    isUserborrow = isUserBorrowed(user_id)
    print(f"status peminjaman kunci user : {isUserborrow[-1]}")
    print(f"id {user_id} melakukan start")
    print(data) 

    if isUserborrow[-1] == 0:
        keyboard = [
        [InlineKeyboardButton("Kembalikan Kunci", callback_data='return_keys')],
        ]
    elif data is not None and data['is_registered'] == 1:
        keyboard = [
        [InlineKeyboardButton("Ketersedian Kunci", callback_data='show_keys')],
        [InlineKeyboardButton("Peminjaman Kunci", callback_data='keys_borrowed')],
        ]
    elif data is not None and data['is_registered'] == 0:
        keyboard = [
        [InlineKeyboardButton("Notify Team Lead", callback_data='notify')],
        ]
    else:
        register_user(user_id, username)
        keyboard = [
            [InlineKeyboardButton("Register", callback_data='register')],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Selamat datang di layanan manajemen kunci! Silakan pilih menu di bawah ini untuk melanjutkan:", 
        reply_markup=reply_markup
    )

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

async def handle_registration(update: Update, context: CallbackContext):
    _, id_register, validasi = update.callback_query.data.split("_")
    print(id_register)
    
    if validasi == "approve":
        update_registration_status(id_register, True)
        await context.bot.send_message(chat_id=id_register, text=f"Anda telah berhasil menjadi user")
    else:
        await context.bot.send_message(chat_id=id_register, text=f"Permintaan anda ditolak")

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

async def handle_notify(update: Update, context: CallbackContext):
    _, __, validasi , id_register = update.callback_query.data.split("_")

    if validasi == "approve":
        update_registration_status(id_register, True)
        await context.bot.send_message(chat_id=id_register, text=f"Anda telah berhasil menjadi user")
    else:
        await context.bot.send_message(chat_id=id_register, text=f"Permintaan anda ditolak")

async def request_key_name(update: Update, context: CallbackContext):
    await update.callback_query.message.reply_text("Masukkan nama kunci yang ingin Anda pinjam:")


async def forward_chat_request(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    key_name = update.message.text
    if update.message.text.split('-')[0] == 'ODC':
        validasi = isKeysOdcAvailable(key_name)

        if validasi is not None and validasi['is_key_available'] == 1:
            keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"borrow_approve_{user_id}_{key_name}")],
            [InlineKeyboardButton("Reject", callback_data=f"borrow_reject_{user_id}_{key_name}")]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id='5168019992', text=f"Request peminjaman kunci:\nUser: @{username}\nKunci: {key_name}\nPlease approve or reject this request.", reply_markup=reply_markup)
        if validasi is not None and validasi['is_key_available'] == 0:
            await context.bot.send_message(chat_id=user_id, text=f"Permintaan peminjaman kunci '{key_name}' telah digunakan orang lain")
        if validasi is None: 
            await context.bot.send_message(chat_id=user_id, text=f"Kunci dengan code '{key_name}' tidak ditemukan")
    else:
        print(update.message.text)


async def handle_borrow_approval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    _, action, user_id, key_name = query.data.split("_")
    dataODC = isKeysOdcAvailable(key_name)

    if action == "approve":
        borrow_key(user_id, key_name,dataODC['Data_ID'])
        await context.bot.send_message(chat_id=user_id, text=f"*Keterangan*:\n\nStatus Peminjaman: *Approve*\nODC Name: *{key_name}*\nLocation: [Google Maps](https://www.google.com/maps?q={dataODC['Latitude']},{dataODC['Longitude']})\n\nHarap ambil kunci anda pada Team Leader Region",parse_mode='markdown')
    else:
        await context.bot.send_message(chat_id=user_id, text=f"Permintaan peminjaman kunci {key_name} Anda telah ditolak.")


async def returnKeys_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keyboard = [
            [InlineKeyboardButton("Pengembalian Kunci", callback_data=f"keys_returning")],
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("", reply_markup=reply_markup) 

async def handle_returnKeyLogbook(update: Update, context: CallbackContext):
    user_id = update.callback_query.from_user.id
    isUserborrow = isUserBorrowed(user_id)
    data = isKeysOdcAvailable(data_id=isUserborrow[1])
    print(data)
    keyboard = [
            [InlineKeyboardButton("Setujui dan lengkapi", callback_data=f"Logbook")],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text=f"*Tatacara pengembalian* :\n\n1. Informasikan kegiatan yang anda lakukan di {data['Nama']} :\n2. Upload Foto Kondisi ODC sebelum pekerjaan (*tampak dalam*)\n3. Upload Foto Kondisi ODC setelah pekerjaan (*tampak dalam*)\n4. Upload Foto Kondisi ODC telah tertutup dan terkunci kembali (*tampak depan*)", parse_mode='markdown',reply_markup=reply_markup)
    
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)
    print(f"sesi approval :{query.data}")

    if query.data == 'register':
        await register_callback(update, context)
    elif query.data.split('_')[0] == 'regist':
        await handle_registration(update, context)
    elif query.data == 'notify':
        await notify_callback(update,context)
    elif query.data.split('_')[0] == 'alert':
        await handle_notify(update,context)
    elif query.data == 'keys_borrowed':
        await request_key_name(update,context)
    elif query.data.startswith('borrow'):
        await handle_borrow_approval(update, context)
    elif query.data == 'return_keys':
        await handle_returnKeyLogbook(update, context)
    # elif query.data == 'Logbook':


def main():
    application = Application.builder().token("7367838125:AAGFZMDYE0le6VjZtlqzzLiECjWCT12rDFA").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_chat_request))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
