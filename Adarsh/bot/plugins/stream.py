import re
import os
import asyncio
import json
import html
from pathlib import Path
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import humanbytes
from Adarsh.vars import Var
from urllib.parse import quote_plus, urlencode
from pyrogram import filters, Client
from pyrogram.enoms import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Adarsh.utils.file_properties import get_name, get_hash
from helper_func import encode, get_message_id, decode, get_messages

db = Database(Var.DATABASE_URL, Var.name)
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "False") == "True"
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

# Create HTML templates directory
HTML_TEMPLATES_DIR = Path("templates")
HTML_TEMPLATES_DIR.mkdir(exist_ok=True)

# HTML template for video pages
VIDEO_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .video-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .generate-btn {{
            background-color: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin: 20px 0;
        }}
        .generate-btn:hover {{
            background-color: #0056b3;
        }}
        .video-player {{
            width: 100%;
            margin-top: 20px;
            display: none;
        }}
        .loading {{
            display: none;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="video-container">
        <h1>{title}</h1>
        <p>Click the button below to generate a fresh streaming link</p>
        <button class="generate-btn" onclick="generateStreamLink()">Generate Streaming Link</button>
        <div class="loading" id="loading">Generating link, please wait...</div>
        <div id="player-container"></div>
    </div>

    <script>
        function generateStreamLink() {{
            document.querySelector('.generate-btn').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            
            fetch('/generate_stream', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    file_id: '{file_id}',
                    file_name: '{file_name}',
                    original_msg_id: {original_msg_id},
                    chat_id: {chat_id}
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                document.getElementById('loading').style.display = 'none';
                if (data.success) {{
                    // Create video player
                    const playerContainer = document.getElementById('player-container');
                    playerContainer.innerHTML = `
                        <video class="video-player" controls autoplay>
                            <source src="${{data.stream_url}}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                        <p><a href="${{data.stream_url}}" target="_blank">Direct link</a></p>
                    `;
                    document.querySelector('.video-player').style.display = 'block';
                }} else {{
                    alert('Error: ' + data.message);
                    document.querySelector('.generate-btn').style.display = 'block';
                }}
            }})
            .catch(error => {{
                document.getElementById('loading').style.display = 'none';
                document.querySelector('.generate-btn').style.display = 'block';
                alert('Error generating stream link: ' + error);
            }});
        }}
    </script>
</body>
</html>
"""

async def process_message(msg, json_output, skipped_messages):
    """Process individual message and generate HTML page"""
    try:
        # Validate media content
        if not (msg.document or msg.video or msg.audio):
            raise ValueError("No media content found in message")
        
        # Prepare caption with fallbacks
        if msg.caption:
            caption = msg.caption.html
            # Clean caption: remove URLs, mentions, hashtags and extra spaces
            caption = re.sub(r'(https?://\S+|@\w+|#\w+)', '', caption)
            caption = re.sub(r'\s+', ' ', caption).strip()
        else:
            # Fallback to filename if no caption
            caption = get_name(msg) or "NEXTPULSE"
        
        # Store original message info for later use
        file_id = get_hash(msg)
        file_name = get_name(msg) or "video"
        original_msg_id = msg.id
        chat_id = msg.chat.id
        
        # Create HTML page for this video
        safe_title = html.escape(caption[:60] + "..." if len(caption) > 60 else caption)
        html_content = VIDEO_HTML_TEMPLATE.format(
            title=safe_title,
            file_id=file_id,
            file_name=html.escape(file_name),
            original_msg_id=original_msg_id,
            chat_id=chat_id
        )
        
        # Save HTML file
        html_filename = f"{file_id}.html"
        html_filepath = HTML_TEMPLATES_DIR / html_filename
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Store mapping in database for later use
        await db.save_file_info(
            file_id, 
            original_msg_id, 
            chat_id, 
            file_name, 
            caption
        )
        
        # Generate URL to the HTML page
        html_url = f"{Var.URL}video/{html_filename}"
        
        # Add to successful output
        json_output.append({
            "title": caption,
            "htmlUrl": html_url,
            "fileId": file_id,
            "fileName": file_name
        })
        
    except Exception as e:
        # Capture details for skipped messages
        file_name = get_name(msg) or "Unknown"
        skipped_messages.append({
            "id": msg.id,
            "file_name": file_name,
            "reason": str(e)
        })

@StreamBot.on_message(filters.private & filters.user(list(Var.OWNER_ID)) & filters.command('batch'))
async def batch(client: Client, message: Message):
    Var.reset_batch()
    json_output = []
    skipped_messages = []

    # Get first and last messages
    try:
        first_message = await client.ask(
            text="Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
            chat_id=message.from_user.id,
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        f_msg_id = await get_message_id(client, first_message)
        if not f_msg_id:
            await first_message.reply("❌ Error\n\nInvalid Forward or Link. Try again.")
            return

        second_message = await client.ask(
            text="Forward the Last Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
            chat_id=message.from_user.id,
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        s_msg_id = await get_message_id(client, second_message)
        if not s_msg_id:
            await second_message.reply("❌ Error\n\nInvalid Forward or Link. Try again.")
            return
    except Exception as e:
        await message.reply(f"❌ Setup Error: {str(e)}")
        return

    # Determine message range
    start_id = min(f_msg_id, s_msg_id)
    end_id = max(f_msg_id, s_msg_id)
    total_messages = end_id - start_id + 1
    status_msg = await message.reply_text(f"🚀 Starting batch processing...\nTotal: {total_messages} messages")
    
    # Process messages in batches
    batch_size = 50
    processed_count = 0
    
    for batch_start in range(start_id, end_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_id)
        msg_ids = list(range(batch_start, batch_end + 1))
        
        try:
            messages = await get_messages(client, msg_ids)
        except Exception as e:
            messages = []
            # If batch fetch fails, get messages individually
            for msg_id in msg_ids:
                try:
                    msg = (await get_messages(client, [msg_id]))[0]
                    messages.append(msg)
                except:
                    messages.append(None)
        
        for msg in messages:
            processed_count += 1
            if not msg:
                skipped_messages.append({
                    "id": msg_ids[messages.index(msg)] if msg in messages else "Unknown",
                    "file_name": "Unknown",
                    "reason": "Message not found"
                })
                continue
                
            await process_message(msg, json_output, skipped_messages)
            if processed_count % 10 == 0:
                await status_msg.edit_text(
                    f"🔄 Processing...\n"
                    f"Progress: {processed_count}/{total_messages}\n"
                    f"Success: {len(json_output)} | Skipped: {len(skipped_messages)}"
                )

    # Prepare final output
    output_data = {
        "successful": json_output,
        "skipped": skipped_messages
    }
    
    # Save to file
    filename = f"/tmp/batch_output_{message.from_user.id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    # Send results
    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=f"✅ Batch processing complete!\n"
                f"Total: {total_messages} | "
                f"Success: {len(json_output)} | "
                f"Skipped: {len(skipped_messages)}\n\n"
                f"HTML pages are available at: {Var.URL}video/"
    )
    await status_msg.delete()
    os.remove(filename)

# Add this to your web server routes (assuming you're using a web framework like Flask)
"""
@app.route('/generate_stream', methods=['POST'])
async def generate_stream():
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
"""

@StreamBot.on_message((filters.private) & (filters.document | filters.audio | filters.photo), group=3)
async def private_receive_handler(c: Client, m: Message):
    if bool(CUSTOM_CAPTION) and bool(m.document):
        caption = CUSTOM_CAPTION.format(
            previouscaption="" if not m.caption else m.caption.html,
            filename=get_name(m)
        )
    else:
        caption = m.caption.html if m.caption else get_name(m)
    caption = re.sub(r'@[\w_]+|http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', caption)
    caption = re.sub(r'\s+', ' ', caption.strip())
    caption = re.sub(r'\s*#\w+', '', caption)

    try:
        log_msg = await m.copy(chat_id=Var.BIN_CHANNEL)
        await asyncio.sleep(0.5)
        
        # Generate HTML page for single file too
        file_id = get_hash(m)
        file_name = get_name(m) or "video"
        safe_title = html.escape(caption[:60] + "..." if len(caption) > 60 else caption)
        
        html_content = VIDEO_HTML_TEMPLATE.format(
            title=safe_title,
            file_id=file_id,
            file_name=html.escape(file_name),
            original_msg_id=m.id,
            chat_id=m.chat.id
        )
        
        # Save HTML file
        html_filename = f"{file_id}.html"
        html_filepath = HTML_TEMPLATES_DIR / html_filename
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Store mapping in database
        await db.save_file_info(
            file_id, 
            m.id, 
            m.chat.id, 
            file_name, 
            caption
        )
        
        # Generate URL to the HTML page
        html_url = f"{Var.URL}video/{html_filename}"
        
        # Send HTML link to user instead of direct stream link
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("WATCH VIDEO", url=html_url)]])
        await m.reply_text(
            text=f"✅ Your file is ready!\n\nClick the button below to watch:\n\n{caption}",
            reply_markup=reply_markup,
            quote=True
        )
        
    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)
