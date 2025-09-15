import re
import os
import asyncio
import json
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import humanbytes
from Adarsh.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from Adarsh.utils.file_properties import get_name, get_hash
from helper_func import encode, get_message_id, decode, get_messages

db = Database(Var.DATABASE_URL, Var.name)
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = os.environ.get('PROTECT_CONTENT', "False") == "True"
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'


# ------------------------
# Helper: Generate HTML Page
# ------------------------
def generate_html_page(msg_id, caption, output_dir="/tmp/watchpages"):
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"{msg_id}.html")

    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{caption}</title>
  <style>
    body {{ display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; background: #f4f4f9; }}
    button {{ padding: 15px 30px; font-size: 18px; cursor: pointer; border: none; border-radius: 10px; background: #008cff; color: white; }}
    button:hover {{ background: #0066cc; }}
  </style>
</head>
<body>
  <button onclick="generateStream()">Generate Stream</button>

  <script>
    async function generateStream() {{
      try {{
        const res = await fetch('/generate?id={msg_id}');
        const data = await res.json();
        if (data.stream_link) {{
          window.location.href = data.stream_link;
        }} else {{
          alert("Failed to generate stream link!");
        }}
      }} catch (err) {{
        alert("Error generating stream link!");
      }}
    }}
  </script>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename


# ------------------------
# Process Message
# ------------------------
async def process_message(msg, json_output, skipped_messages):
    try:
        if not (msg.document or msg.video or msg.audio):
            raise ValueError("No media content found in message")

        if msg.caption:
            caption = msg.caption.html
            caption = re.sub(r'(https?://\S+|@\w+|#\w+)', '', caption)
            caption = re.sub(r'\s+', ' ', caption).strip()
        else:
            caption = get_name(msg) or "NEXTPULSE"

        # ✅ Forward once to BIN_CHANNEL (same as before)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_msg = await msg.copy(
                    chat_id=Var.BIN_CHANNEL,
                    caption=caption[:1024],
                    parse_mode=ParseMode.HTML
                )
                break
            except FloodWait as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(e.x)
                else:
                    raise
        else:
            raise Exception("Max retries exceeded for FloodWait")

        # ✅ Instead of saving direct stream_link, create watch page
        html_file = generate_html_page(log_msg.id, caption)

        # ✅ Save link to that HTML page in JSON
        watch_page_url = f"{Var.URL}watchpages/{log_msg.id}.html"

        json_output.append({
            "title": caption,
            "watchPage": watch_page_url
        })

    except Exception as e:
        file_name = get_name(msg) or "Unknown"
        skipped_messages.append({
            "id": msg.id,
            "file_name": file_name,
            "reason": str(e)
        })


# ------------------------
# Batch Command
# ------------------------
@StreamBot.on_message(filters.private & filters.user(list(Var.OWNER_ID)) & filters.command('batch'))
async def batch(client: Client, message: Message):
    Var.reset_batch()
    json_output = []
    skipped_messages = []

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

    start_id = min(f_msg_id, s_msg_id)
    end_id = max(f_msg_id, s_msg_id)
    total_messages = end_id - start_id + 1
    status_msg = await message.reply_text(f"🚀 Starting batch processing...\nTotal: {total_messages} messages")

    batch_size = 50
    processed_count = 0

    for batch_start in range(start_id, end_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_id)
        msg_ids = list(range(batch_start, batch_end + 1))

        try:
            messages = await get_messages(client, msg_ids)
        except:
            messages = []
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

    output_data = {
        "successful": json_output,
        "skipped": skipped_messages
    }

    filename = f"/tmp/batch_output_{message.from_user.id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=f"✅ Batch processing complete!\n"
                f"Total: {total_messages} | "
                f"Success: {len(json_output)} | "
                f"Skipped: {len(skipped_messages)}"
    )
    await status_msg.delete()
    os.remove(filename)
