import asyncio
from bot.telegram_bot import bot
from website.routes import app
from database import Database
import os

db = Database(os.getenv("DATABASE_URL"))

async def run_bot():
    await bot.start()
    print("Bot started")
    await asyncio.sleep(3600)  # Keep the bot running for 1 hour (or adjust as needed)
    await bot.stop()
    print("Bot stopped")

async def run_web():
    await app.run_task(host='0.0.0.0', port=os.getenv('PORT', 5000))

async def main():
    # Create tasks for bot and web server
    bot_task = asyncio.create_task(run_bot())
    web_task = asyncio.create_task(run_web())

    # Wait for both tasks to complete
    await asyncio.gather(bot_task, web_task)

if __name__ == "__main__":
    # Use the same event loop for both Quart and Pyrogram
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
