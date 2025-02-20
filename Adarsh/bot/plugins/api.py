import os
from flask import Flask, request, jsonify
from Adarsh.bot import StreamBot  # Import your bot client
from Adarsh.utils.file_properties import get_name, get_hash
from Adarsh.vars import Var  # Import environment variables

app = Flask(__name__)

@app.route('/generate_stream', methods=['GET'])
def generate_stream():
    message_id = request.args.get('msg_id')

    if not message_id:
        return jsonify({"error": "Message ID required"}), 400

    try:
        client = StreamBot  # Use your bot client
        msg = client.get_messages(chat_id=int(Var.DB_CHANNEL), message_ids=int(message_id))
        stream_link = f"{Var.URL}watch/{str(msg.id)}/{get_name(msg)}?hash={get_hash(msg)}"

        return jsonify({"stream_link": stream_link})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
