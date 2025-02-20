from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Base URL of your Telegram streaming bot
STREAM_BOT_URL = os.getenv("STREAM_BOT_URL", "https://nextpulse-25b1b64cdf4e.herokuapp.com")

@app.route('/')
def home():
    return "Streaming API is running!"

@app.route('/generate_stream', methods=['GET'])
def generate_stream():
    msg_id = request.args.get('msg_id')
    if not msg_id:
        return jsonify({"error": "Missing msg_id parameter"}), 400

    try:
        # Construct Telegram video link
        telegram_link = f"https://t.me/c/2024354927/{msg_id}"
        
        # Generate streaming link using your bot
        stream_link = f"{STREAM_BOT_URL}/stream/{msg_id}"
        
        return jsonify({"stream_link": stream_link})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
