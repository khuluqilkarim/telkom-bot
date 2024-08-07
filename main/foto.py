from telegram import InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import Update

# Dictionary to store user submissions
user_submissions = {}

async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_submissions[user_id] = {"photos": [], "message": None}
    await update.message.reply_text("Please send up to 3 photos and then a message describing the logbook.")

async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_submissions:
        if len(user_submissions[user_id]["photos"]) < 3:
            user_submissions[user_id]["photos"].append(update.message.photo[-1].file_id)
            if len(user_submissions[user_id]["photos"]) == 3:
                await update.message.reply_text("You have sent 3 photos. Now, please send your logbook message.")
        else:
            await update.message.reply_text("You have already sent 3 photos. Please send your logbook message.")
    else:
        await update.message.reply_text("Please start by sending the /start command.")

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in user_submissions:
        if user_submissions[user_id]["message"] is None:
            user_submissions[user_id]["message"] = update.message.text
            await update.message.reply_text("Logbook message received. Preparing to send everything to the team leader.")
            # Forward photos and message to team leader
            await forward_to_team_leader(update, context, user_id)
            # Clear submission
            del user_submissions[user_id]
        else:
            await update.message.reply_text("You have already sent your logbook message.")
    else:
        await update.message.reply_text("Please start by sending the /start command.")

async def forward_to_team_leader(update: Update, context: CallbackContext, user_id: int):
    team_leader_id = '5168019992'  # Replace with your team leader's chat ID
    submission = user_submissions.get(user_id)
    
    if submission:
        photos = submission["photos"]
        message = submission["message"]
        
        try:
            # Send media group (photos)
            media_group = [InputMediaPhoto(media=photo_id) for photo_id in photos]
            await context.bot.send_media_group(chat_id=team_leader_id, media=media_group)
            
            # Send logbook message
            await context.bot.send_message(chat_id=team_leader_id, text=message)
            
            print("Submission sent to team leader successfully.")
        except Exception as e:
            print(f"Error sending message or photos: {e}")
    else:
        print("No submission found for user:", user_id)

def main():
    application = Application.builder().token("7367838125:AAGFZMDYE0le6VjZtlqzzLiECjWCT12rDFA").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
