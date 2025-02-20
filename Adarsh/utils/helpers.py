from typing import Any
from pyrogram.types import Message

def get_media_from_message(message: Message) -> Any:
    """Extracts media (photo, video, document, etc.) from a message."""
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
    return None

def get_hash(media_msg: Message) -> str:
    """Returns a unique identifier for the media."""
    media = get_media_from_message(media_msg)
    return getattr(media, "file_unique_id", "")[:6] if media else ""

def get_name(media_msg: Message) -> str:
    """Extracts file name from the message, falling back to caption."""
    media = get_media_from_message(media_msg)
    file_name = getattr(media, 'file_name', "")
    
    if not file_name and media_msg.caption:
        return media_msg.caption.html
    return file_name
