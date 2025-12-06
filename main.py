import discord
import os
import sys
import asyncio
from roast_cog import RoastMasterCog
from google import genai

# --- 1. Essential Configuration & Validation ---

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check for missing environment variables
if not DISCORD_TOKEN:
    print("FATAL ERROR: DISCORD_TOKEN environment variable is missing.")
    sys.exit(1)
if not GEMINI_API_KEY:
    print("FATAL ERROR: GEMINI_API_KEY environment variable is missing.")
    sys.exit(1)

# Initialize Gemini Client
try:
    GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"FATAL ERROR: Failed to initialize Gemini Client. Check GEMINI_API_KEY. Error: {e}")
    sys.exit(1)


# --- 2. Discord Client Setup (Intents) ---
intents = discord.Intents.default()
# CRITICAL INTENTS: MUST be enabled in Discord Developer Portal
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

# --- 3. Client Events and Cog Loading ---

# Global cog instance to ensure setup runs only once
roast_master_cog = None
cog_setup_complete = False

@client.event
async def on_ready():
    global roast_master_cog, cog_setup_complete
    
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Bot is ready to listen!')
    sys.stdout.flush()
    
    # Only setup the cog once (on first connection)
    if not cog_setup_complete:
        try:
            roast_master_cog = RoastMasterCog(client, GEMINI_CLIENT)
            await roast_master_cog.setup()
            cog_setup_complete = True
            print('RoastMaster cog initialized and ready!')
            sys.stdout.flush()
        except Exception as e:
            print(f'ERROR during cog setup: {e}')
            sys.stdout.flush()
    else:
        print('Reconnected - cog already initialized.')
        sys.stdout.flush()

if __name__ == '__main__':
    
    # Start the Discord client
    asyncio.run(client.start(DISCORD_TOKEN))
