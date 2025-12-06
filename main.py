import discord
import os
import sys
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from roast_cog import RoastMasterCog
from google import genai

# --- 0. Render Health Check Server ---
# This server satisfies Render's requirement to bind to a port (usually 10000)
# It's necessary to prevent the 'No open ports' error.
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is active.")

def start_http_server():
    """Starts the dummy server in a separate thread."""
    try:
        # Render provides the port via the PORT environment variable
        port = int(os.environ.get('PORT', 10000))
        httpd = HTTPServer(('', port), HealthCheckHandler)
        print(f"Starting dummy HTTP server on port {port}...")
        httpd.serve_forever()
    except Exception as e:
        print(f"Error starting HTTP server (non-fatal): {e}")


# --- 1. Essential Configuration & Validation ---

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check for missing environment variables
required_vars = {
    "DISCORD_TOKEN": DISCORD_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
}

for key, value in required_vars.items():
    if value is None:
        print(f"FATAL ERROR: Required environment variable '{key}' is missing in Render settings.")
        sys.exit(1)

# Initialize Gemini Client
try:
    GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"FATAL ERROR: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
    sys.exit(1)


# --- 2. Discord Client Setup (Intents) ---
# Intent configuration is CRITICAL for the bot to read messages.
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  # MUST be enabled in Discord Developer Portal

client = discord.Client(intents=intents)

# --- 3. Client Events and Cog Loading ---

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Bot is ready and roasting in all channels!')
    
    # Load the Cog
    roast_master_cog = RoastMasterCog(client, GEMINI_CLIENT)
    
    # Manually call setup to attach listeners and start the task
    await roast_master_cog.setup()

if __name__ == '__main__':
    
    # 3a. Start the dummy HTTP server in a separate thread FIRST
    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True 
    http_thread.start()

    # 3b. Start the Discord client
    if DISCORD_TOKEN:
        asyncio.run(client.start(DISCORD_TOKEN))
    else:
        print("Discord token is missing. Bot cannot start.")
