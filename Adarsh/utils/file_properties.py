from pyrogram import Client
from typing import Any, Optional
from pyrogram.types import Message
from pyrogram.file_id import FileId
from pyrogram.raw.types.messages import Messages
from Adarsh.server.exceptions import FIleNotFound
from Adarsh.utils.helpers import get_file_ids  # ✅ Import from helpers.py

async def parse_file_id(message: "Message") -> Optional[FileId]:
    media = get_media_from_message(message)
    if media:
        return FileId.decode(media.file_id)

async def parse_file_unique_id(message: "Messages") -> Optional[str]:
    media = get_media_from_message(message)
    if media:
        return media.file_unique_id

def get_media_from_message(message: "Message") -> Any:
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )
    for attr in media_types:
        media = getattr(message, attr, None)
        if media:
            return media

def get_hash(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6]

def get_name(media_msg: Message) -> str:
    media = get_media_from_message(media_msg)
    file_name = getattr(media, 'file_name', "")

    # If file_name is absent, use the caption as a fallback
    if not file_name and media_msg.caption:
        return media_msg.caption.html
    else:
        return file_name

def get_media_file_size(m):
    media = get_media_from_message(m)
    return getattr(media, "file_size", 0)
