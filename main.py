import asyncio
import signal
from bot.telegram_bot import bot
from website.routes import app
from database import Database
import os

db = Database(os.getenv("DATABASE_URL"))

async def run_bot():
    await bot.start()
    print("Bot started")
    await asyncio.sleep(3600)  # Keep the bot running
    await bot.stop()
    print("Bot stopped")

async def run_web():
    await app.run_task(host='0.0.0.0', port=os.getenv('PORT', 5000))

async def shutdown(signal, loop):
    print(f"Received exit signal {signal.name}...")
    await bot.stop()
    await db.close()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main():
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig, loop)))
    
    # Create tasks for bot and web server
    bot_task = asyncio.create_task(run_bot())
    web_task = asyncio.create_task(run_web())

    # Wait for both tasks to complete
    await asyncio.gather(bot_task, web_task)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
