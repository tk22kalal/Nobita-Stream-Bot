from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/get_file_ids', methods=['GET'])
def get_file_ids_handler():
    """Handles request to get file IDs."""
    try:
        from Adarsh.utils.file_properties import get_file_ids  # Import inside function to avoid circular import
        file_ids = get_file_ids()
        return jsonify({"file_ids": file_ids})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """Basic API homepage"""
    return "Welcome to the API!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Heroku's assigned port
    app.run(host="0.0.0.0", port=port)
