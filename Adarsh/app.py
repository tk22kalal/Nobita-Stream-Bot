import asyncio
import re
from flask import Flask, request, jsonify
from pyrogram import Client
from Adarsh.bot import StreamBot
from Adarsh.vars import Var
from Adarsh.utils.helpers import get_name, get_hash
from helper_func import get_messages
from pyrogram.errors import FloodWait

app = Flask(__name__)  # Flask API to handle stream requests

async def process_video(video_url):
    try:
        # Extract Message ID from the Telegram video link
        match = re.search(r"https://t\.me/c/(\d+)/(\d+)", video_url)
        if not match:
            return {"error": "Invalid Telegram video link format."}

        chat_id = int(f"-100{match.group(1)}")  # Convert to valid chat ID
        message_id = int(match.group(2))

        # Fetch the original message using the extracted message ID
        messages = await get_messages(StreamBot, [message_id])
        if not messages or len(messages) == 0:
            return {"error": "Error: Could not fetch the message. Ensure it's from a valid private channel."}

        original_msg = messages[0]  # Extract message

        # Forward the original message to BIN_CHANNEL
        log_msg = await original_msg.forward(Var.BIN_CHANNEL)
        await asyncio.sleep(0.5)  # Small delay for safety

        # Generate the stream link
        stream_link = f"{Var.URL}watch/{log_msg.id}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        return {"stream_link": stream_link}

    except FloodWait as e:
        print(f"FloodWait: Sleeping for {e.x} seconds")
        await asyncio.sleep(e.x)
        return {"error": "FloodWait occurred, please try again later."}

    except Exception as e:
        print(f"Error: {e}")
        return {"error": "An error occurred while processing the video link."}

@app.route('/get_stream', methods=['GET'])
async def get_stream():
    video_url = request.args.get("video_url")
    if not video_url:
        return jsonify({"error": "Missing video_url parameter."})

    result = await process_video(video_url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
