import re
import os
import asyncio
import json
from asyncio import TimeoutError
from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import humanbytes
from Adarsh.vars import Var
from urllib.parse import quote_plus
from pyrogram import filters, Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telethon.tl.types import InputPeerChannel
from Adarsh.utils.file_properties import get_name, get_hash, get_media_file_size
db = Database(Var.DATABASE_URL, Var.name)
from helper_func import encode, get_message_id, decode, get_messages

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", None) == 'True'

MY_PASS = os.environ.get("MY_PASS", None)
pass_dict = {}
pass_db = Database(Var.DATABASE_URL, "ag_passwords")


import openpyxl
from io import BytesIO

@StreamBot.on_message(filters.private & filters.user(list(Var.OWNER_ID)) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(
                text="Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return

        f_msg_id = await get_message_id(client, first_message)

        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or the link is invalid.")
            continue

    while True:
        try:
            second_message = await client.ask(
                text="Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return

        s_msg_id = await get_message_id(client, second_message)

        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nThis Forwarded Post is not from my DB Channel or the link is invalid.")
            continue

    message_links = []
    for msg_id in range(min(f_msg_id, s_msg_id), max(f_msg_id, s_msg_id) + 1):
        string = f"get-{msg_id * abs(client.db_channel)}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"
        message_links.append(link)

    json_output = []

    for link in message_links:
        try:
            base64_string = link.split("=", 1)[1]
            decoded_string = await decode(base64_string)
        except Exception as e:
            print(f"Error decoding link: {e}")
            return

        argument = decoded_string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel))
                end = int(int(argument[2]) / abs(client.db_channel))
            except:
                return
            ids = list(range(start, end + 1)) if start <= end else list(range(start, end - 1, -1))
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel))]
            except:
                return

        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            print(f"Error fetching messages: {e}")
            await message.reply_text("Something went wrong while fetching messages.")
            return        

        for msg in messages:
            if bool(CUSTOM_CAPTION) and bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption=msg.caption.html if msg.caption else "",
                    filename=msg.document.file_name
                )
            else:
                caption = msg.caption.html if msg.caption else ""

            caption = re.sub(r'@[\w_]+|http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', caption)
            caption = re.sub(r'\s+', ' ', caption.strip())

            try:
                log_msg = await msg.copy(chat_id=Var.BIN_CHANNEL)
                await asyncio.sleep(0.5)
                stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                json_output.append({
                    "title": caption,
                    "streamingUrl": stream_link
                })

            except FloodWait as e:
                print(f"Sleeping for {str(e.x)}s")
                await asyncio.sleep(e.x)

    # Save JSON to file
    filename = f"/tmp/batch_output_{message.from_user.id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=4, ensure_ascii=False)

    # Send file to user
    await client.send_document(
        chat_id=message.chat.id,
        document=filename,
        caption="✅ Batch JSON created successfully.",
    )


@StreamBot.on_message((filters.private) & (filters.document | filters.audio | filters.photo), group=3)
async def private_receive_handler(c: Client, m: Message):
    if bool(CUSTOM_CAPTION) and bool(m.document):
        caption = CUSTOM_CAPTION.format(
            previouscaption="" if not m.caption else m.caption.html,
            filename=m.video.file_name
        )
    else:
        caption = m.caption.html if m.caption else get_name(m.video)
    caption = re.sub(r'@[\w_]+|http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', caption)
    caption = re.sub(r'\s+', ' ', caption.strip())
    caption = re.sub(r'\s*#\w+', '', caption)

    try:
        log_msg = await m.copy(chat_id=Var.BIN_CHANNEL)
        await asyncio.sleep(0.5)
        stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        download_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("STREAM ⏯️", url=stream_link)]])
        await log_msg.edit_reply_markup(reply_markup)        
        F_text = f"<tr><td>&lt;a href='{download_link}' target='_blank'&gt; {caption} &lt;/a&gt;</td></tr>"
        text = f"<tr><td>{F_text}</td></tr>"
        X = await m.reply_text(text=f"{text}", disable_web_page_preview=True, quote=True)
        await asyncio.sleep(3)
    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)

@StreamBot.on_message((filters.private) & (filters.video | filters.audio | filters.photo), group=3)
async def private_receive_handler(c: Client, m: Message):
    if bool(CUSTOM_CAPTION) and bool(m.video):
        caption = CUSTOM_CAPTION.format(
            previouscaption="" if not m.caption else m.caption.html,
            filename=m.video.file_name
        )
    else:
        caption = m.caption.html if m.caption else get_name(m.video)
    caption = re.sub(r'@[\w_]+|http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', caption)
    caption = re.sub(r'\s+', ' ', caption.strip())

    try:
        log_msg = await m.copy(chat_id=Var.BIN_CHANNEL)
        await asyncio.sleep(0.5)
        stream_link = f"{Var.URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
        download_link = f"{Var.URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("STREAM ⏯️", url=stream_link)]])
        await log_msg.edit_reply_markup(reply_markup)        
        F_text = f"<tr><td>&lt;a href='{stream_link}' target='_blank'&gt; {caption} &lt;/a&gt;</td></tr>"
        text = f"<tr><td>{F_text}</td></tr>"
        X = await m.reply_text(text=f"{text}", disable_web_page_preview=True, quote=True)
    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)
