from aiohttp import web

async def hello(request):
    return web.Response(text="Hello, World!")

# Add this handler for favicon.ico
async def favicon_handler(request):
    # Return an empty response (no icon), status 204 means "No Content"
    return web.Response(status=204)

app = web.Application()
app.router.add_get('/', hello)
app.router.add_get('/favicon.ico', favicon_handler)  # <-- Add this line

if __name__ == '__main__':
    web.run_app(app)
