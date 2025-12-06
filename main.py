import discord
import os
import sys
from roast_cog import RoastMasterCog
from google import genai
import asyncio

# --- 1. Essential Configuration & Validation ---
# (Same validation as before, ensuring robust startup)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WELCOME_CHANNEL_ID_STR = os.getenv("WELCOME_CHANNEL_ID")

# Check for missing environment variables
required_vars = {
    "DISCORD_TOKEN": DISCORD_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "WELCOME_CHANNEL_ID": WELCOME_CHANNEL_ID_STR,
}

for key, value in required_vars.items():
    if value is None:
        print(f"FATAL ERROR: Required environment variable '{key}' is missing in Render settings.")
        sys.exit(1)

# Convert and validate WELCOME_CHANNEL_ID
try:
    WELCOME_CHANNEL_ID = int(WELCOME_CHANNEL_ID_STR)
except ValueError:
    print(f"FATAL ERROR: WELCOME_CHANNEL_ID '{WELCOME_CHANNEL_ID_STR}' is not a valid number. Check Render settings.")
    sys.exit(1)

# Initialize Gemini Client (used by the Cog)
try:
    GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"FATAL ERROR: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
    sys.exit(1)


# --- 2. Discord Client Setup (Intents) ---

# We use discord.Client since we are not using command prefixes.
intents = discord.Intents.default()
# PRIVILEGED INTENTS (MUST be enabled in Discord Developer Portal)
intents.members = True          
intents.message_content = True  # CRITICAL: Required for reading mentions and replies

# Initialize the Client
client = discord.Client(intents=intents)

# --- 3. Client Events and Cog Loading ---

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Bot is ready and roasting!')
    
    # Load the Cog with the necessary data
    roast_master_cog = RoastMasterCog(client, GEMINI_CLIENT, WELCOME_CHANNEL_ID)
    
    # Run the setup function on the Cog to attach event listeners and start the task
    await roast_master_cog.setup()

    # NOTE: Since discord.Client doesn't support Cogs directly, 
    # we call the setup method manually, which starts the task and sets listeners.

if __name__ == '__main__':
    if DISCORD_TOKEN:
        # Use asyncio.run to launch the client
        asyncio.run(client.start(DISCORD_TOKEN))
    else:
        print("Discord token is missing. Bot cannot start.")
