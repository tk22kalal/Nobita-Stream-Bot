
from helper_func import encode, get_message_id, decode, get_messages
import os
from urllib.parse import quote_plus
from Adarsh.bot import StreamBot
from Adarsh.vars import Var

async def generate_stream_link(video_id):
    try:
        # Import inside function to prevent circular import error
        from Adarsh.utils.file_properties import get_name, get_hash  

        # Convert video ID to integer
        video_id = int(video_id)
        
        # Fetch the message from the DB_CHANNEL
        messages = await get_messages(StreamBot, [video_id])

        if not messages:
            return None  # Video not found
        
        msg = messages[0]

        # Generate stream link
        stream_link = f"{Var.URL}watch/{msg.id}/{quote_plus(get_name(msg))}?hash={get_hash(msg)}"
        return stream_link
    
    except Exception as e:
        print(f"Error generating stream link: {e}")
        return None
