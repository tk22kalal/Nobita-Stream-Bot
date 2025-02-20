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
