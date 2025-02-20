from quart import Quart, jsonify, request
from database import Database
import os

app = Quart(__name__)
db = Database(os.getenv("DATABASE_URL"))

@app.route('/process', methods=['POST'])
async def process_link():
    data = await request.get_json()
    telegram_link = data['telegram_link']
    lecture_name = data['lecture_name']
    
    # Check if already processed
    existing = await db.get_stream_link(lecture_name)
    if existing and existing != "pending":
        return jsonify({"stream_link": existing})
    
    # Trigger bot processing
    await db.insert_file(
        file_name=lecture_name,
        telegram_link=telegram_link,
        stream_link="pending"
    )
    
    # Start background task
    await process_telegram_link(telegram_link, lecture_name)
    
    return jsonify({"stream_link": "pending"})

@app.route('/check-status/<lecture_name>')
async def check_status(lecture_name):
    link = await db.get_stream_link(lecture_name)
    return jsonify({"stream_link": link})
