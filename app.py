from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

# Retrieve your bot's username from the environment.
# Make sure to set BOT_USERNAME in your Heroku configuration (without the "@" symbol).
BOT_USERNAME = os.environ.get("BOT_USERNAME", "default_bot_username")
if BOT_USERNAME == "default_bot_username":
    print("WARNING: BOT_USERNAME is not set correctly in your environment!")

@app.route("/")
def index():
    start_param = request.args.get("start")
    if start_param:
        # Construct the Telegram deep-link URL.
        deep_link = f"tg://resolve?domain={BOT_USERNAME}&start={start_param}"
        # Build the HTML page with meta-refresh and JavaScript redirection.
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Launching Telegram...</title>
            <!-- Fallback meta-refresh (2-second delay) -->
            <meta http-equiv="refresh" content="2; url={deep_link}">
            <script type="text/javascript">
                function redirectToTelegram() {{
                    window.location.href = "{deep_link}";
                    window.location.replace("{deep_link}");
                }}
                window.onload = function() {{
                    setTimeout(redirectToTelegram, 500);
                }};
            </script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding-top: 50px;
                }}
            </style>
        </head>
        <body>
            <p>Attempting to open Telegram...</p>
            <p>If nothing happens, please <a href="{deep_link}">click here</a>.</p>
        </body>
        </html>
        """
        return render_template_string(html_content)
    else:
        return "No 'start' parameter provided. This service is for Telegram deep‑link redirection."

@app.route("/favicon.ico")
def favicon():
    # Return a 204 No Content response to avoid 404 errors.
    return "", 204

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
