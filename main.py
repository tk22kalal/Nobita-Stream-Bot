import asyncio
from bot.telegram_bot import bot
from website.routes import app
from database import Database

db = Database(os.getenv("DATABASE_URL"))

async def run_bot():
    await bot.start()
    await bot.stop()

async def main():
    # No need to call db.connect() for MongoDB
    server_task = asyncio.create_task(app.run_task(host='0.0.0.0', port=os.getenv('PORT', 5000)))
    bot_task = asyncio.create_task(run_bot())
    await asyncio.gather(server_task, bot_task)

if __name__ == "__main__":
    asyncio.run(main())
