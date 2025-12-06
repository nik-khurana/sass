import discord
import os
import sys
from roast_cog import RoastMasterCog
from google import genai
import asyncio

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

# We use discord.Client for event-only handling (no commands)
intents = discord.Intents.default()
# PRIVILEGED INTENTS (MUST be enabled in Discord Developer Portal)
intents.members = True          
intents.message_content = True  

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
    if DISCORD_TOKEN:
        asyncio.run(client.start(DISCORD_TOKEN))
    else:
        print("Discord token is missing. Bot cannot start.")
