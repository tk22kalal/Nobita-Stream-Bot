from flask import Flask, request, jsonify, render_template
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def get_streaming_link(msg_id):
    if msg_id == "45546":  # Example valid msg_id
        return f"https://nextpulse-25b1b64cdf4e.herokuapp.com/stream/{msg_id}"
    return None

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/generate_stream', methods=['GET'])
def generate_stream():
    msg_id = request.args.get('msg_id')
    app.logger.info(f"Received request with msg_id: {msg_id}")

    if not msg_id:
        app.logger.error("Missing msg_id parameter")
        return jsonify({"error": "Missing msg_id parameter"}), 400

    stream_url = get_streaming_link(msg_id)
    
    if stream_url:
        app.logger.info(f"Streaming link generated: {stream_url}")
        return jsonify({"stream_url": stream_url})
    else:
        app.logger.error(f"No streaming link found for msg_id: {msg_id}")
        return jsonify({"error": "Streaming link not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
