from flask import Flask, request, jsonify
import asyncio
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from Adarsh.vars import Var
from Adarsh.utils.file_properties import get_name, get_hash
from pyrogram.enons import ParseMode
from pyrogram.errors import FloodWait

# Ensure these objects are imported or initialized as in your bot file
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database

db = Database(Var.DATABASE_URL, Var.name)
client = StreamBot  # Or however your bot client is named/initialized

app = Flask(__name__)

@app.route('/generate_stream', methods=['POST'])
def generate_stream():
    async def async_generate():
        try:
            data = await request.get_json()
            file_id = data.get('file_id')
            original_msg_id = data.get('original_msg_id')
            chat_id = data.get('chat_id')
            
            # Get file info from database
            file_info = await db.get_file_info(file_id)
            if not file_info:
                return jsonify({'success': False, 'message': 'File not found'})
            
            # Get the original message
            original_msg = await client.get_messages(chat_id, original_msg_id)
            if not original_msg:
                return jsonify({'success': False, 'message': 'Original message not found'})
            
            # Forward to log channel with FloodWait handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    log_msg = await original_msg.copy(
                        chat_id=Var.BIN_CHANNEL,
                        caption=file_info['caption'][:1024],
                        parse_mode=ParseMode.HTML
                    )
                    break
                except FloodWait as e:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(e.x)
                    else:
                        raise
            
            # Generate fresh streaming URL
            file_name = get_name(log_msg) or file_info['file_name']
            file_hash = get_hash(log_msg)
            stream_link = f"{Var.URL}watch/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"
            
            # Update database with new log message ID
            await db.update_log_message_id(file_id, log_msg.id)
            
            return jsonify({
                'success': True,
                'stream_url': stream_link,
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
            })
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    # Run async handler
    return asyncio.run(async_generate())
