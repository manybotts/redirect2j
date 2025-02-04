import os
from aiohttp import web

# Get the bot's username from the environment (without "@")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "default_bot_username")
if BOT_USERNAME == "default_bot_username":
    print("WARNING: BOT_USERNAME is not set! Please set it in Heroku.")

async def redirect_handler(request):
    """Handles deep-link redirection to Telegram"""
    start_param = request.query.get("start")
    if start_param:
        # Build the Telegram deep-link
        deep_link = f"tg://resolve?domain={BOT_USERNAME}&start={start_param}"
        print(f"Redirecting to: {deep_link}")

        # Return an HTML page that auto-redirects to Telegram
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
                }}
                setTimeout(redirectToTelegram, 500);
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

async def favicon_handler(request):
    """Handles favicon requests to avoid 404 errors."""
    return web.Response(status=204)

# Create the aiohttp application and register routes
app = web.Application()
app.router.add_get("/", redirect_handler)
app.router.add_get("/{tail:.*}", redirect_handler)
app.router.add_get("/favicon.ico", favicon_handler)

if __name__ == "__main__":
    # Bind to Heroku's provided PORT
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
