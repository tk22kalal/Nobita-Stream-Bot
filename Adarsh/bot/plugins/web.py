from fastapi import FastAPI, Request
from Adarsh.vars import Var
from Adarsh.utils.file_properties import get_name, get_hash
from urllib.parse import quote_plus

app = FastAPI()

@app.get("/generate")
async def generate_stream(id: int):
    try:
        # Forward message again to BIN_CHANNEL
        msg = await app.bot.get_messages(Var.DB_CHANNEL, id)
        log_msg = await msg.copy(chat_id=Var.BIN_CHANNEL)

        file_name = get_name(log_msg) or "NEXTPULSE"
        file_hash = get_hash(log_msg)
        fqdn_url = Var.get_url_for_file(str(log_msg.id))

        stream_link = f"{fqdn_url}watch/{log_msg.id}/{quote_plus(file_name)}?hash={file_hash}"

        return {"stream_link": stream_link}

    except Exception as e:
        return {"error": str(e)}
