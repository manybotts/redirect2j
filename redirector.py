import os
import json
import pymongo
from aiohttp import web

# Retrieve bot usernames from environment variable (JSON format)
BOT_USERNAMES_JSON = os.environ.get("BOT_USERNAMES", '{}')
try:
    BOT_USERNAMES = json.loads(BOT_USERNAMES_JSON)  # Convert JSON string to dictionary
except json.JSONDecodeError:
    BOT_USERNAMES = {}
    print("ERROR: Invalid JSON format in BOT_USERNAMES environment variable!")

if not BOT_USERNAMES:
    print("WARNING: No bot usernames are set! Please configure BOT_USERNAMES in Heroku.")

# Connect to MongoDB with a dedicated database name
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://username:password@cluster0.mongodb.net/?retryWrites=true&w=majority")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "telegram_redirector")  # Default database name
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]  # Use the specified database name
collection = db["redirect_links"]

async def list_bots_handler(request):
    """Returns all available bot redirect links in HTML or JSON format."""
    host = request.host  # Get current domain name
    bot_links = {
        bot_name: f"https://{host}/bot/{bot_name}/?start=YOUR_PAYLOAD"
        for bot_name in BOT_USERNAMES
    }

    # JSON Response
    if request.query.get("format") == "json":
        return web.json_response({"available_bots": bot_links})

    # HTML Page Display
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Available Telegram Bots</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding-top: 20px; }
            .container { max-width: 600px; margin: auto; padding: 20px; border-radius: 8px; background: #f9f9f9; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); }
            h2 { color: #333; }
            .bot-link { margin: 10px 0; padding: 10px; background: #007bff; color: #fff; border-radius: 5px; display: inline-block; text-decoration: none; }
            .bot-link:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Available Telegram Bots</h2>
    """
    
    for bot_name, bot_url in bot_links.items():
        html_content += f'<p><strong>{bot_name}:</strong> <a class="bot-link" href="{bot_url}" target="_blank">Open Link</a></p>'
    
    html_content += "</div></body></html>"
    
    return web.Response(text=html_content, content_type="text/html")

async def redirect_handler(request):
    """Handles Telegram deep-link redirection."""
    bot_name = request.match_info.get("bot_name")
    start_param = request.query.get("start")

    if bot_name in BOT_USERNAMES:
        bot_username = BOT_USERNAMES[bot_name]
        if start_param:
            deep_link = f"tg://resolve?domain={bot_username}&start={start_param}"
            print(f"Redirecting to: {deep_link}")

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Redirecting to Telegram...</title>
                <meta http-equiv="refresh" content="2; url={deep_link}">
                <script>
                    function redirectToTelegram() {{
                        window.location.href = "{deep_link}";
                        setTimeout(() => window.close(), 1000);
                    }}
                    window.onload = function() {{
                        setTimeout(redirectToTelegram, 500);
                    }};
                </script>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }}
                </style>
            </head>
            <body>
                <p>Redirecting to Telegram...</p>
                <p>If nothing happens, <a href="{deep_link}">click here</a>.</p>
            </body>
            </html>
            """
            return web.Response(text=html_content, content_type="text/html")
        else:
            return web.Response(text="Missing 'start' parameter.", content_type="text/plain")
    else:
        return web.Response(text=f"Bot '{bot_name}' is not configured.", content_type="text/plain", status=404)

async def favicon_handler(request):
    """Handles favicon requests to avoid 404 errors."""
    return web.Response(status=204)

# Create the aiohttp application and register routes
app = web.Application()
app.router.add_get("/", list_bots_handler)  # Show bot URLs in a clean HTML page
app.router.add_get("/bot/{bot_name}/", redirect_handler)  # Maintains original long URL structure
app.router.add_get("/favicon.ico", favicon_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
