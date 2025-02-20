from pyrogram import Client
from typing import Optional
from pyrogram.types import Message
from pyrogram.file_id import FileId
from Adarsh.server.exceptions import FIleNotFound
from Adarsh.utils.helper import get_media_from_message  # Import from helper.py

async def parse_file_id(message: Message) -> Optional[FileId]:
    """Decodes FileId from a message."""
    media = get_media_from_message(message)
    return FileId.decode(media.file_id) if media else None

async def parse_file_unique_id(message: Message) -> Optional[str]:
    """Returns unique file ID."""
    media = get_media_from_message(message)
    return media.file_unique_id if media else None

async def get_file_ids(client: Client, chat_id: int, msg_id: int) -> Optional[FileId]:
    """Fetches file details from a message ID."""
    message = await client.get_messages(chat_id, msg_id)
    if not message or message.empty:
        raise FIleNotFound

    media = get_media_from_message(message)
    if not media:
        return None

    file_unique_id = await parse_file_unique_id(message)
    file_id = await parse_file_id(message)

    setattr(file_id, "file_size", getattr(media, "file_size", 0))
    setattr(file_id, "mime_type", getattr(media, "mime_type", ""))
    setattr(file_id, "file_name", getattr(media, "file_name", ""))
    setattr(file_id, "unique_id", file_unique_id)

    return file_id
