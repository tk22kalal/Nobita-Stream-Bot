from helper_func import encode, get_message_id, decode, get_messages
import os
from urllib.parse import quote_plus
from Adarsh.bot import StreamBot
from Adarsh.vars import Var
from Adarsh.utils.helpers import get_name, get_hash  # Import from helpers.py

async def generate_stream_link(video_id):
    try:
        # Convert video ID to integer
        video_id = int(video_id)
        
        # Fetch the message from the DB_CHANNEL
        messages = await get_messages(StreamBot, [video_id])

        # Ensure messages is not None or empty
        if not messages or len(messages) == 0:
            print(f"Error: No message found for video_id {video_id}")
            return None  # Video not found

        msg = messages[0]  # Extract first message

        # Generate stream link
        stream_link = f"{Var.URL}watch/{msg.id}/{quote_plus(get_name(msg))}?hash={get_hash(msg)}"
        return stream_link
    
    except Exception as e:
        print(f"Error generating stream link: {e}")
        return None
