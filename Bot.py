import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Replace with your bot token
BOT_TOKEN = '8095711658:AAEV0Y7_Z5DljAcD6kmkpK9HtM3qgwwzP5I'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Choose an upload service:")
    await show_upload_services(update)

async def show_upload_services(update: Update):
    keyboard = [
        [InlineKeyboardButton("GoFile", callback_data='gofile')],
        [InlineKeyboardButton("File.io", callback_data='fileio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select an upload service:", reply_markup=reply_markup)

async def handle_upload_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['upload_service'] = query.data  # Store selected service
    await query.edit_message_text(text=f"Service selected: {query.data}. Now send me any file!")

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_service = context.user_data.get('upload_service')
    
    if not selected_service:
        await update.message.reply_text("Please select an upload service first using /start.")
        return

    # Handle any type of file (not just documents)
    if update.message.document or update.message.audio or update.message.video or update.message.photo:
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
            original_filename = f"{update.message.photo[-1].file_id}.jpg"
        else:
            file = await update.message.document.get_file() if update.message.document else await update.message.audio.get_file() if update.message.audio else await update.message.video.get_file()
            original_filename = update.message.document.file_name if update.message.document else f"{update.message.audio.file_id}.mp3" if update.message.audio else f"{update.message.video.file_id}.mp4"

        file_path = await file.download_as_bytearray()

        if selected_service == 'gofile':
            await upload_to_gofile(update, original_filename, file_path)
        elif selected_service == 'fileio':
            await upload_to_fileio(update, original_filename, file_path)
    else:
        await update.message.reply_text("Please send a file (document, audio, video, or photo).")

async def upload_to_gofile(update: Update, original_filename, file_path):
    # Step 1: Get available servers
    server_response = requests.get('https://api.gofile.io/servers')
    if server_response.status_code != 200:
        await update.message.reply_text("Error connecting to the GoFile service. Please try later.")
        return

    server_data = server_response.json()
    print("Server response:", server_data)  # Debug line

    # Check if the data is available and contains servers
    if server_data.get("status") == "ok" and server_data["data"].get("servers"):
        server = server_data["data"]["servers"][0]["name"]
    else:
        await update.message.reply_text("Failed to retrieve servers. Please try again.")
        return

    # Step 2: Upload the file to the selected server with original filename
    upload_response = requests.post(
        f'https://{server}.gofile.io/contents/uploadFile',
        files={'file': (original_filename, file_path)}
    )

    if upload_response.status_code == 200:
        upload_data = upload_response.json()
        if upload_data["status"] == "ok":
            download_link = upload_data["data"]["downloadPage"]
            await update.message.reply_text(f"File uploaded successfully to GoFile! Download link: {download_link}")
        else:
            await update.message.reply_text("Upload failed. Please try again.")
    else:
        await update.message.reply_text("Error uploading the file to GoFile. Please try again.")

async def upload_to_fileio(update: Update, original_filename, file_path):
    # Step 1: Upload the file to file.io
    upload_response = requests.post('https://file.io', files={'file': (original_filename, file_path)})

    if upload_response.status_code == 200:
        upload_data = upload_response.json()
        if upload_data.get("success"):
            download_link = upload_data["link"]
            await update.message.reply_text(f"File uploaded successfully to File.io! Download link: {download_link}")
        else:
            await update.message.reply_text("Upload failed. Please try again.")
    else:
        await update.message.reply_text("Error uploading the file to File.io. Please try again.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_upload_service_selection))
    app.add_handler(MessageHandler(filters.ALL, upload_file))  # Accept any file type

    print("Bot is running...")
    app.run_polling()
