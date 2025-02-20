import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database import Database
from urllib.parse import quote_plus

db = Database(os.getenv("DATABASE_URL"))

class StreamBot(Client):
    def __init__(self):
        super().__init__(
            "stream_bot",
            api_id=int(os.getenv("API_ID")),
            api_hash=os.getenv("API_HASH"),
            bot_token=os.getenv("BOT_TOKEN")
        )

    async def start(self):
        await super().start()
        await db.create_table()
        print("Bot started")

    async def stop(self):
        await super().stop()
        await db.close()
        print("Bot stopped")

bot = StreamBot()

@bot.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file_upload(client, message: Message):
    try:
        file_name = message.document.file_name if message.document else message.video.file_name
        file_hash = str(hash(file_name))
        
        # Forward to channel
        log_msg = await message.copy(int(os.getenv("BIN_CHANNEL")))
        
        # Generate links
        stream_link = f"{os.getenv('URL')}watch/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
        
        # Store in database
        await db.insert_file(
            file_name=file_name,
            message_id=log_msg.id,
            file_hash=file_hash,
            stream_link=stream_link
        )
        
        # Send confirmation
        await message.reply_text(f"File stored successfully!\nStream Link: {stream_link}")

    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("Error processing file. Please try again.")

if __name__ == "__main__":
    bot.run()
