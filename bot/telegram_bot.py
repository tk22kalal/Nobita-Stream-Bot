import os
from pyrogram import Client
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

# Initialize the bot
bot = StreamBot()

async def process_telegram_link(telegram_link, lecture_name):
    try:
        # Extract channel ID and message ID from link
        parts = telegram_link.split('/')
        channel_id = int(parts[-2])
        message_id = int(parts[-1])
        
        # Forward to bin channel
        forwarded_msg = await bot.forward_messages(
            chat_id=int(os.getenv("BIN_CHANNEL")),
            from_chat_id=channel_id,
            message_ids=message_id
        )
        
        # Generate streaming link
        stream_link = f"{os.getenv('URL')}watch/{forwarded_msg.id}/{quote_plus(lecture_name)}"
        
        # Update database
        await db.insert_file(
            file_name=lecture_name,
            telegram_link=telegram_link,
            stream_link=stream_link
        )
        
        return stream_link
    except Exception as e:
        print(f"Error processing link: {e}")
        return "pending"
