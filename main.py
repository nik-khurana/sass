import discord
from discord.ext import commands
import os
import sys
from roast_cog import RoastMasterCog
from google import genai

# --- 1. Essential Configuration & Validation ---
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

# --- 2. Discord Bot Setup (Intents) ---

intents = discord.Intents.default()
# PRIVILEGED INTENTS (MUST be enabled in Discord Developer Portal)
intents.members = True          # Required for on_member_join
intents.message_content = True  # CRITICAL: Required to read all messages, mentions, and replies

bot = commands.Bot(command_prefix='!', intents=intents)

# --- 3. Run the Bot ---

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot is ready and roasting!')
    
    # Add the Cog (features) once the bot is ready
    await bot.add_cog(RoastMasterCog(bot, GEMINI_CLIENT, WELCOME_CHANNEL_ID))

if __name__ == '__main__':
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Discord token is missing. Bot cannot start.")
