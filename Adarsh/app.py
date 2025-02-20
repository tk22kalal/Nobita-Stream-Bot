import os
import logging
from aiohttp import web
from Adarsh.stream import generate_stream_link

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_stream(request):
    video_id = request.query.get("video_id")
    
    if not video_id:
        return web.json_response({"error": "Missing video_id"}, status=400)
    
    try:
        stream_link = await generate_stream_link(video_id)
        
        if stream_link:
            return web.json_response({"stream_link": stream_link})
        else:
            return web.json_response({"error": "Stream link not found"}, status=404)
    
    except Exception as e:
        logger.error(f"Error fetching stream link: {e}")
        return web.json_response({"error": "Internal Server Error"}, status=500)

# Create an aiohttp application
app = web.Application()
app.router.add_get('/get_stream', get_stream)

# Ensure the app binds to the correct port on Heroku
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))  # Get PORT from environment variable
    web.run_app(app, host="0.0.0.0", port=port)
