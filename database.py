from motor.motor_asyncio import AsyncIOMotorClient
import os

class Database:
    def __init__(self, database_url):
        self.client = AsyncIOMotorClient(database_url)
        self.db = self.client.get_database("stream_bot")
        self.files = self.db.get_collection("files")

    async def create_table(self):
        # MongoDB doesn't require table creation
        pass

    async def insert_file(self, file_name, message_id, file_hash, stream_link):
        await self.files.update_one(
            {"file_name": file_name},
            {"$set": {
                "message_id": message_id,
                "file_hash": file_hash,
                "stream_link": stream_link
            }},
            upsert=True
        )

    async def get_all_files(self):
        return await self.files.find({}, {"_id": 0, "file_name": 1, "stream_link": 1}).to_list(None)

    async def get_stream_link(self, file_name):
        result = await self.files.find_one({"file_name": file_name}, {"_id": 0, "stream_link": 1})
        return result["stream_link"] if result else None

    async def close(self):
        self.client.close()
