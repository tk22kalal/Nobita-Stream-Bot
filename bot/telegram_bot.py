import os
from pyrogram import Client
from database import Database

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

# Export the bot object
__all__ = ["bot"]
