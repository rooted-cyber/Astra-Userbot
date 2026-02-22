import os
import subprocess
from aiohttp import web

async def health_check(request):
    """Simple health check endpoint for Render to prevent the web service from sleeping/failing."""
    return web.Response(text="Astra Userbot Web Environment is healthy and active.", status=200)

app = web.Application()
app.router.add_get('/', health_check)
app.router.add_get('/health', health_check)

if __name__ == '__main__':
    # Start the actual Astra Userbot in a separate subprocess
    print("🚀 Booting Astra Userbot in background...")
    bot_process = subprocess.Popen(["python", "bot.py"])
    
    # Start the dummy web server required by Render's Web Service specifications
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting Render Web Service bind on port {port}...")
    
    try:
        web.run_app(app, host='0.0.0.0', port=port)
    finally:
        # Gracefully shut down the bot if the web server stops
        print("🛑 Terminating bot process...")
        bot_process.terminate()
        bot_process.wait()
