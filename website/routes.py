import os  # Add this at the top
from database import Database
from quart import Quart, jsonify
from database import Database

app = Quart(__name__)
db = Database(os.getenv("DATABASE_URL"))

@app.route("/api/files")
async def api_files():
    files = await db.get_all_files()
    return jsonify([dict(file) for file in files])

@app.route("/api/files/<file_name>")
async def api_file(file_name):
    link = await db.get_stream_link(file_name)
    return jsonify({"stream_link": link})

if __name__ == "__main__":
    app.run()
