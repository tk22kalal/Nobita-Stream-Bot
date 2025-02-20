from pyrogram import Client
from typing import Optional
from pyrogram.file_id import FileId
from Adarsh.server.exceptions import FIleNotFound
from Adarsh.utils.helpers import get_media_from_message, parse_file_id, parse_file_unique_id

async def get_file_ids(client: Client, chat_id: int, id: int) -> Optional[FileId]:
    message = await client.get_messages(chat_id, id)
    if message.empty:
        raise FIleNotFound
    
    media = get_media_from_message(message)
    file_unique_id = await parse_file_unique_id(message)
    file_id = await parse_file_id(message)

    if file_id:
        setattr(file_id, "file_size", getattr(media, "file_size", 0))
        setattr(file_id, "mime_type", getattr(media, "mime_type", ""))
        setattr(file_id, "file_name", getattr(media, "file_name", ""))
        setattr(file_id, "unique_id", file_unique_id)

    return file_id
