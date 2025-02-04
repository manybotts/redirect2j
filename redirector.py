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
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "telegram_redirector")
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]  # Use the specified database name
collection = db["redirect_links"]

async def list_bots_handler(request):
    """Displays available bot redirect links in a stylish HTML page with copy buttons."""
    host = request.host  # Get current domain name
    bot_links = {
        bot_name: f"https://{host}/bot/{bot_name}/"
        for bot_name in BOT_USERNAMES
    }

    # JSON Response
    if request.query.get("format") == "json":
        return web.json_response({"available_bots": bot_links})

    # Stylish HTML Page
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Available Telegram Bots</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 20px; background: #f4f4f4; }}
            .container {{ max-width: 600px; margin: auto; padding: 20px; border-radius: 8px; background: #fff; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); }}
            h2 {{ color: #333; }}
            .bot-link {{ display: flex; justify-content: space-between; align-items: center; background: #007bff; color: #fff; padding: 10px; margin: 10px 0; border-radius: 5px; text-decoration: none; }}
            .bot-link:hover {{ background: #0056b3; }}
            .copy-btn {{ background: #28a745; color: #fff; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }}
            .copy-btn:hover {{ background: #218838; }}
        </style>
        <script>
            function copyToClipboard(text) {{
                navigator.clipboard.writeText(text).then(function() {{
                    alert("Copied: " + text);
                }});
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <h2>Available Telegram Bots</h2>
    """

    for bot_name, bot_url in bot_links.items():
        html_content += f'''
            <div class="bot-link">
                <span>{bot_name}</span>
                <button class="copy-btn" onclick="copyToClipboard('{bot_url}')">Copy URL</button>
            </div>
        '''

    html_content += "</div></body></html>"
    
    return web.Response(text=html_content, content_type="text/html")

async def redirect_handler(request):
    """Handles Telegram deep-link redirection with a stylish UI."""
    bot_name = request.match_info.get("bot_name")
    start_param = request.query.get("start")

    if bot_name in BOT_USERNAMES:
        bot_username = BOT_USERNAMES[bot_name]
        if start_param:
            deep_link = f"tg://resolve?domain={bot_username}&start={start_param}"
            print(f"Redirecting to: {deep_link}")

            # Modern Redirect Page
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Fetching Your Files...</title>
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
                    body {{ font-family: Arial, sans-serif; text-align: center; padding-top: 100px; background: linear-gradient(to right, #007bff, #6610f2); color: #fff; }}
                    .container {{ padding: 20px; }}
                    h1 {{ font-size: 36px; text-shadow: 2px 2px 10px rgba(0,0,0,0.2); }}
                    .loader {{ border: 6px solid #f3f3f3; border-radius: 50%; border-top: 6px solid #ffffff; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }}
                    @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Fetching Your Files in Lightning Speeds ⚡</h1>
                    <div class="loader"></div>
                    <p>If nothing happens, <a href="{deep_link}" style="color: yellow;">click here</a>.</p>
                </div>
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
app.router.add_get("/", list_bots_handler)  # Shows bot URLs in a clean HTML page with copy feature
app.router.add_get("/bot/{bot_name}/", redirect_handler)  # Stylish redirect page
app.router.add_get("/favicon.ico", favicon_handler)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
