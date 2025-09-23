
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
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from Adarsh.utils.file_properties import get_name, get_hash

db = Database(Var.DATABASE_URL, Var.name)
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

# ------------------------- PROCESS ONE MESSAGE -------------------------
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

        # copy with retry
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

        file_hash = get_hash(log_msg)
        fqdn_url = Var.get_url_for_file(str(log_msg.id))
        stream_link = f"{fqdn_url}generate/{log_msg.id}?hash={file_hash}"

        json_output.append({
            "title": caption,
            "streamingUrl": stream_link
        })

    except Exception as e:
        file_name = get_name(msg) or "Unknown"
        skipped_messages.append({
            "id": msg.id,
            "file_name": file_name,
            "reason": str(e)
        })


# ------------------------- BATCH HANDLER -------------------------
@StreamBot.on_message(filters.private & filters.user(list(Var.OWNER_ID)) & filters.command('batch'))
async def batch_handler(client: Client, message: Message):
    json_output = []
    skipped_messages = []

    try:
        # ask for first message
        first_message = await client.ask(
            chat_id=message.from_user.id,
            text="Forward the FIRST Message from DB Channel (with Quotes)\n\nor Send the DB Channel Post Link",
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        f_msg_id = await extract_message_id(first_message)

        if not f_msg_id:
            await first_message.reply("❌ Error\n\nInvalid Forward or Link. Try again.")
            return

        # ask for last message
        second_message = await client.ask(
            chat_id=message.from_user.id,
            text="Forward the LAST Message from DB Channel (with Quotes)\n\nor Send the DB Channel Post Link",
            filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
            timeout=60
        )
        s_msg_id = await extract_message_id(second_message)

        if not s_msg_id:
            await second_message.reply("❌ Error\n\nInvalid Forward or Link. Try again.")
            return

    except Exception as e:
        await message.reply(f"❌ Setup Error: {str(e)}")
        return

    # process range
    start_id = min(f_msg_id, s_msg_id)
    end_id = max(f_msg_id, s_msg_id)
    total_messages = end_id - start_id + 1
    status_msg = await message.reply_text(f"🚀 Starting batch...\nTotal: {total_messages} messages")

    batch_size = 50
    processed_count = 0

    for batch_start in range(start_id, end_id + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, end_id)
        msg_ids = list(range(batch_start, batch_end + 1))

        try:
            messages = await client.get_messages(Var.BIN_CHANNEL, msg_ids)
        except Exception:
            messages = []
            for msg_id in msg_ids:
                try:
                    msg = await client.get_messages(Var.BIN_CHANNEL, msg_id)
                    messages.append(msg)
                except:
                    messages.append(None)

        for idx, msg in enumerate(messages):
            processed_count += 1
            if not msg:
                skipped_messages.append({
                    "id": msg_ids[idx],
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

    output_data = {"successful": json_output, "skipped": skipped_messages}

    filename = f"/tmp/batch_output_{message.from_user.id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption=f"✅ Batch complete!\n"
                f"Total: {total_messages} | "
                f"Success: {len(json_output)} | "
                f"Skipped: {len(skipped_messages)}"
    )
    await status_msg.delete()
    os.remove(filename)


# ------------------------- MESSAGE ID EXTRACTOR -------------------------
async def extract_message_id(msg: Message) -> int:
    if msg.forward_from_chat and msg.forward_from_message_id:
        return msg.forward_from_message_id

    if msg.text:
        match = re.search(r"(?:t\.me/|/c/)[A-Za-z0-9_]+/(\d+)", msg.text)
        if match:
            return int(match.group(1))

    return None


# ------------------------- PRIVATE MEDIA HANDLER -------------------------
@StreamBot.on_message((filters.private) & (filters.document | filters.video | filters.audio | filters.photo), group=3)
async def private_media_handler(c: Client, m: Message):
    
    media = m.document or m.video or m.audio or m.photo
    
    if CUSTOM_CAPTION:
        caption = CUSTOM_CAPTION.format(
            previouscaption="" if not m.caption else m.caption.html,
            filename=getattr(media, 'file_name', 'Unknown')
        )
    else:
        caption = m.caption.html if m.caption else getattr(media, 'file_name', 'Unknown')

    caption = re.sub(r'@[\w_]+|https?://\S+|\s*#\w+', '', caption)
    caption = re.sub(r'\s+', ' ', caption.strip())

    try:
        log_msg = await m.copy(chat_id=Var.BIN_CHANNEL)
        await asyncio.sleep(0.5)
        stream_link = f"{Var.URL}generate/{log_msg.id}?hash={get_hash(log_msg)}"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("STREAM ⏯️", url=stream_link)]])
        await log_msg.edit_reply_markup(reply_markup)

        F_text = f"<tr><td>&lt;a href='{stream_link}' target='_blank'&gt; {caption} &lt;/a&gt;</td></tr>"
        await m.reply_text(text=F_text, disable_web_page_preview=True, quote=True)

    except FloodWait as e:
        await asyncio.sleep(e.x)
