from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime

class Database:
    def __init__(self, database_url):
        self.client = AsyncIOMotorClient(database_url)
        self.db = self.client.get_database("stream_bot")
        self.files = self.db.get_collection("files")

    async def insert_file(self, file_name, telegram_link, stream_link):
        await self.files.update_one(
            {"file_name": file_name},
            {"$set": {
                "telegram_link": telegram_link,
                "stream_link": stream_link,
                "timestamp": datetime.now()
            }},
            upsert=True
        )

    async def get_all_files(self):
        return await self.files.find(
            {"stream_link": {"$ne": "pending"}}, 
            {"_id": 0, "file_name": 1, "telegram_link": 1, "stream_link": 1}
        ).to_list(None)

    async def get_stream_link(self, file_name):
        result = await self.files.find_one(
            {"file_name": file_name},
            {"_id": 0, "stream_link": 1}
        )
        return result["stream_link"] if result else None

    async def close(self):
        self.client.close()
