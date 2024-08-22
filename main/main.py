from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, filters, MessageHandler
from telegram import InputMediaPhoto

import os
import json
import random
import string
from datetime import datetime

from helper.database import get_user_by_id, getLogBook, isKeysOdcAvailable, register_user, update_registration_status, borrow_key, return_key, finishReturning, insert_logbook, Update_logbook, isUserBorrowed

user_submissions = {}

def createFolder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    else:
        return False
    
    print(f"\033[93mDEBUG \033[96mcreateFolder\033[0m func :: \033[92msuccess\033[0m")

async def downloadFile(file, file_name):
    try:
        await file.download_to_drive(file_name)
        print(f"\033[93mDEBUG \033[96mdownloadFile\033[0m func :: \033[92msuccess\033[0m")
    except Exception as e:  # Catch general exceptions
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

async def selectCapacity(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keyboard = [
        [InlineKeyboardButton("1", callback_data=f"capacity_1_{user_id}")],
        [InlineKeyboardButton("2", callback_data=f"capacity_2_{user_id}")],
        [InlineKeyboardButton("3", callback_data=f"capacity_3_{user_id}")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text=f"Pilih Berapa jumlah anda ingin meminjam kunci :", reply_markup=reply_markup)

async def handleBorrowCapacity(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    _, total, user_id = query.data.split("_")

    if total == '1':
        user_submissions[int(user_id)]['kapasitas'] = 1
    elif total == '2':
        user_submissions[int(user_id)]['kapasitas'] = 2
    elif total == '3':
        user_submissions[int(user_id)]['kapasitas'] = 3
    else: 
        await context.bot.send_message(chat_id=user_id, text=f"Kapasitas tidak ditemukan")

    await request_key_name(update, context, total)

async def request_key_name(update: Update, context: CallbackContext, total=None):
    query = update.callback_query
    await query.answer()
    if total is not None:
        await update.callback_query.message.reply_text(f"Anda dapat meminjam {total} kunci, silakan masukkan nama kunci yang ingin Anda pinjam :")
        print(f"\033[93mDEBUG \033[96mrequest_key_name\033[0m func :: \033[92msuccess\033[0m")
    else:
        await update.callback_query.message.reply_text(f"silakan masukkan nama kunci yang ingin Anda cari :")

async def forward_chat_request(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    key_name = update.message.text

    # validasi pada bagian ini untuk melakukan pengecekan setiap tl region 

    data = get_user_by_id(user_id)

    if data is None:
        await context.bot.send_message(chat_id=user_id, text=f"Anda belum terdaftar, lakukan /start dan mendaftar")
        return
    elif update.message.text.split('-')[0] == 'ODC':
        validasi = isKeysOdcAvailable(odc_name=key_name)
        randID = user_submissions[user_id]["randID"]
        if validasi is not None and validasi['is_key_available'] == 1 and user_submissions[user_id]['kapasitas'] is not None:
            userKapasitas = user_submissions[user_id]['kapasitas'] 
            userKapasitas -= 1 

            print(f"{user_submissions[user_id]}")

            if user_submissions[user_id]['kapasitas'] > 0:
                user_submissions[user_id]['kapasitas'] = userKapasitas
                print(f"{user_submissions[user_id]}")
                keyboard = [
                    [InlineKeyboardButton("Approve", callback_data=f"borrow_approve_{user_id}_{key_name}_{randID}")],
                    [InlineKeyboardButton("Reject", callback_data=f"borrow_reject_{user_id}_{key_name}_{randID}")]
                ]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=user_id, text=f"Permintaan peminjaman kunci {key_name} telah diajukan.")
                await context.bot.send_message(chat_id=validasi['Lead_Region'], text=f"Request peminjaman kunci:\nUser: @{username}\nKunci: {key_name}\nPlease approve or reject this request.", reply_markup=reply_markup)
            else:
                await context.bot.send_message(chat_id=user_id, text=f"Anda melebihi kapasitas peminjaman")
        else:
            if validasi['link_layout'] is not None:
                await context.bot.send_message(
                    chat_id=user_id, 
                    text=f"*Keterangan*:\n\nODC Name   : *{key_name}*\nLocation       : [Google Maps](https://www.google.com/maps?q={validasi['Latitude']},{validasi['Longitude']})\nLayout          : [Link PDF]({validasi['link_layout']})\n",
                    parse_mode='markdown'
                )
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
        await context.bot.send_message(chat_id=user_id, text=f"*Keterangan*:\n\nStatus Peminjaman: *Approve*\nODC Name: *{key_name}*\nLocation: [📍 Google Maps](https://www.google.com/maps?q={dataODC['Latitude']},{dataODC['Longitude']})\n\nSilakan ambil kunci Anda di lokasi yang telah ditentukan oleh Team Leader Region.",parse_mode='markdown')
        
        if user_submissions[int(user_id)]['kapasitas'] < 0: 
            keyboard = [
                    [InlineKeyboardButton(f"Kembalikan Kunci {key_name}", callback_data=f"returnKeys_{key_name}")],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=user_id,text=
                f"Ajukan Pengembalian kunci {key_name}. Harap isi logbook dan kembalikan kunci setelah tugas selesai.", 
                reply_markup=reply_markup
            )
            
    else:
        userKapasitas = user_submissions[int(user_id)]['kapasitas'] 
        userKapasitas += 1
        
        user_submissions[int(user_id)]['kapasitas'] = userKapasitas
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
    _, key_name, key_id = update.callback_query.data.split('_')

    keyboard = [
            [InlineKeyboardButton("Setuju dan lengkapi", callback_data=f"Logbook_{key_name}_{key_id}")],
        ]
    user_submissions[user_id]['pre-logbook'] = key_name
    print(user_submissions[user_id]['pre-logbook'])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text=f"*Tatacara pengembalian* :\n\n1. Informasikan kegiatan yang anda lakukan di {key_name} :\n2. Upload Foto Kondisi ODC sebelum pekerjaan (*tampak dalam*)\n3. Upload Foto Kondisi ODC setelah pekerjaan (*tampak dalam*)\n4. Upload Foto Kondisi ODC telah tertutup dan terkunci kembali (*tampak depan*)", parse_mode='markdown', reply_markup=reply_markup)
    print(f"\033[93mDEBUG \033[96mhandle_returnKeyLogbook\033[0m func :: \033[92msuccess\033[0m ")

async def logbook(update: Update, context: CallbackContext):
    _, key_name, key_id = update.callback_query.data.split('_')
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

    odc_name = user_submissions[user_id]["pre-logbook"]
    randID = user_submissions[user_id]["randID"]
    key_id = isKeysOdcAvailable(odc_name=odc_name)


    keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"keyReturn_approve_{user_id}_{odc_name}_{randID}_{key_id['Data_ID']}")],
            [InlineKeyboardButton("Reject", callback_data=f"keyReturn_reject_{user_id}_{odc_name}_{randID}_{key_id['Data_ID']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    now = datetime.now()

    if submission:
        photos = submission["photos"]
        message = submission["message"]

        iskeyreturn = getLogBook(user_submissions[user_id]['randID'],user_id)

        if iskeyreturn is not None:
            Update_logbook(message,randID)
        else:
            insert_logbook(user_id,odc_name,message, randID)
        
        text = f"*Logbook* :\nKey : *{odc_name}*\nWaktu : *{now.strftime("%Y-%m-%d %H:%M:%S")}*\n\nPesan :\n{message}"

        try:
            media_group = [InputMediaPhoto(media=photo_id) for photo_id in photos]
            await context.bot.send_media_group(chat_id=key_id['Lead_Region'], media=media_group, caption=text, parse_mode='markdown')
            await context.bot.send_message(chat_id=key_id['Lead_Region'],text=f"Request pengembalian kunci:\nUser: @{username}\nKey : {odc_name}",reply_markup=reply_markup)

        except Exception as e:
            print(f"\033[91mError \033[96mforward_to_team_leader\033[0m func :: {e}")
    else:
        print("No submission found for user:", user_id)

    print(f"\033[93mDEBUG \033[96mforward_to_team_leader\033[0m func :: \033[92msuccess\033[0m")
    
async def handle_returnKey_approval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, action, user_id, key_name, randID, key_id = query.data.split("_")
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
            [InlineKeyboardButton("Pengembalian selesai", callback_data=f"USRkeys_{user_id}_{key_name}_{randID}_{key_id}")]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=user_id, text=f"Logbook disetujui. Harap kembalikan kunci {dataODC['Nama']} segera.",reply_markup=reply_markup)

        user_submissions[int(user_id)]['file_photos'] = []
        user_submissions[int(user_id)]['photos'] = []
        user_submissions[int(user_id)]['message'] = None
        user_submissions[int(user_id)]['pre-logbook'] = None
        user_submissions[int(user_id)]['kapasitas'] = None


        print(user_submissions[int(user_id)])
    else:
        await context.bot.send_message(chat_id=user_id, text=f"Logbook ditolak. Harap isi kembali.")
        user_submissions[int(user_id)]['file_photos'] = []
        user_submissions[int(user_id)]['photos'] = []
        user_submissions[int(user_id)]['message'] = None
        user_submissions[int(user_id)]['pre-logbook'] = None
        user_submissions[int(user_id)]['kapasitas'] = None


        print(user_submissions[int(user_id)])
        
        print(f"\033[93mDEBUG \033[96muser_submissions\033[0m data :: \033[92m{user_submissions[int(user_id)]}\033[0m")

    print(f"\033[93mDEBUG \033[96mhandle_returnKey_approval\033[0m func :: \033[92msuccess\033[0m")

async def handle_finishReturnKeys_approval(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, user_id, key_name, randID, key_id = query.data.split("_")
    data_user = get_user_by_id(user_id)
    Lead_id = isKeysOdcAvailable(odc_name=key_name)


    keyboard = [
            [InlineKeyboardButton("Sudah", callback_data=f"TLkeys_approve_{user_id}_{key_name}_{randID}_{key_id}")],
            [InlineKeyboardButton("Belum", callback_data=f"TLkeys_reject_{user_id}_{key_name}_{randID}_{key_id}")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=Lead_id['Lead_Region'], text=f"Apakah user ini @{data_user['username']} telah mengembalikan kunci {key_name}?", reply_markup=reply_markup)
    
async def finishReturnKeys_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    _, action, user_id, key_name, randID, key_id = query.data.split("_")

    isUserborrow_json = isUserBorrowed(int(user_id))

    isUserborrow = None
    if isUserborrow_json is not None:
        isUserborrow = json.loads(isUserborrow_json)

    if action == 'approve':
        finishReturning(user_id, key_id, randID)
        await context.bot.send_message(chat_id=user_id, text=f"Terimakasih telah mengembalikan.")
        if isUserborrow is None:
            del user_submissions[int(user_id)]

    elif action == 'reject':
        await returningKeysButton(user_id, key_name, context, randID, key_id)
        
async def returningKeysButton(user_id, key_name, context, randID, key_id):
    keyboard = [
            [InlineKeyboardButton("Pengembalian selesai", callback_data=f"USRkeys_{user_id}_{key_name}_{randID}_{key_id}")]
            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=user_id, text=f"Harap kembalikan kunci {key_name} segera.",reply_markup=reply_markup)


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
        await selectCapacity(update,context)
    elif query.data == 'show_keys':
        await request_key_name(update, context)
    elif query.data.split('_')[0] == 'capacity':
        await handleBorrowCapacity(update, context)
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
            "randID": None,
            "kapasitas": None,
            "pre-logbook": None
        }

    print(f"\n\033[91mDEBUG \033[96muser_submissions\033[0m data is None :: \033[93m{user_submissions[user_id]}\033[0m")

    if user_submissions[user_id]["randID"] is None:
        user_submissions[user_id]["randID"] = generateID()

    print(f"\033[93mDEBUG \033[96muser_submissions\033[0m data Created :: \033[92m{user_submissions[user_id]}\033[0m")

    data = get_user_by_id(user_id)
    isUserborrow_json = isUserBorrowed(int(user_id))
    iskeyreturn = getLogBook(user_submissions[user_id]['randID'], user_id)
    print(f"iskeyreturn start :: {iskeyreturn}")

    isUserborrow = None
    if isUserborrow_json is not None:
        try:
            isUserborrow = json.loads(isUserborrow_json)
            print(isUserborrow)
        except json.JSONDecodeError as e:
            print(f"\033[91mError \033[96misUserBorrowed\033[0m func :: JSON decoding error: {e}")

    if iskeyreturn is not None and iskeyreturn['is_approve'] == 0:
        if isUserborrow is not None:
            keyboard = []
            for borrowed_item in isUserborrow:
                data_ODC = isKeysOdcAvailable(data_id=int(borrowed_item['key_id']))

                if data_ODC:
                    keyboard.append([InlineKeyboardButton(f"Kembalikan Kunci {data_ODC['Nama']}", callback_data=f"returnKeys_{data_ODC['Nama']}_{borrowed_item['key_id']}")])

            if keyboard:
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "Anda meminjam kunci berikut. Harap isi logbook dan kembalikan kunci setelah tugas selesai:", 
                    reply_markup=reply_markup
                )
            else:
                print("No valid keys found for return.")
        else:
            print("isUserborrow is None, cannot retrieve key data.")
    
    elif iskeyreturn is not None and iskeyreturn['is_approve'] == 0:
        if isUserborrow is not None:
            for borrowed_item in isUserborrow:
                if borrowed_item['is_returned'] == 0:
                    data_ODC = isKeysOdcAvailable(data_id=int(borrowed_item['key_id']))
                    if data_ODC:
                        await returningKeysButton(
                            user_id=user_id,
                            key_name=data_ODC['Nama'],
                            context=context,
                            randID=user_submissions[user_id]['randID'],
                            key_id=borrowed_item['key_id']
                        )
                    else:
                        print(f"Data ODC tidak tersedia untuk key_id {borrowed_item['key_id']}.")
        else:
            print("isUserborrow is None, cannot retrieve key data.")
    
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
