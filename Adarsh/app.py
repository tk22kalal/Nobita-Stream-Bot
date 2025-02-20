from aiohttp import web
from Adarsh.stream import generate_stream_link

async def get_stream(request):
    video_id = request.query.get("video_id")
    
    if not video_id:
        return web.json_response({"error": "Missing video_id"}, status=400)
    
    stream_link = await generate_stream_link(video_id)
    
    if stream_link:
        return web.json_response({"stream_link": stream_link})
    else:
        return web.json_response({"error": "Stream link not found"}, status=404)

app = web.Application()
app.router.add_get('/get_stream', get_stream)

if __name__ == '__main__':
    web.run_app(app, host="0.0.0.0", port=8080)
