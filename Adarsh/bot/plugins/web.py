from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/generate-link')
def generate_link():
    msg_id = request.args.get('msg_id')
    # Logic to generate fresh link for the Telegram video (msg_id)
    # For example, call the bot's API or generate using the latest logic
    fresh_link = generate_streaming_link(msg_id)  # Implement this
    return jsonify({"streamingUrl": fresh_link})
