import asyncpg
import os

class Database:
    def __init__(self, database_url):
        self.db_url = database_url
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.db_url)

    async def create_table(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id SERIAL PRIMARY KEY,
                    file_name TEXT UNIQUE,
                    message_id INTEGER,
                    file_hash TEXT,
                    stream_link TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')

    async def insert_file(self, file_name, message_id, file_hash, stream_link):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO files (file_name, message_id, file_hash, stream_link)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (file_name) DO UPDATE SET
                message_id = EXCLUDED.message_id,
                file_hash = EXCLUDED.file_hash,
                stream_link = EXCLUDED.stream_link
            ''', file_name, message_id, file_hash, stream_link)

    async def get_all_files(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT file_name, stream_link FROM files ORDER BY created_at DESC")

    async def get_stream_link(self, file_name):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT stream_link FROM files WHERE file_name = $1",
                file_name
            )

    async def close(self):
        await self.pool.close()
