import discord
from discord.ext import commands
from google import genai
import os
import sys

# --- Configuration & Setup ---

# Load environment variables. If any are missing, the script will halt immediately.
# We are intentionally NOT using python-dotenv here, as Render handles the environment
# variables directly, and relying on os.getenv is safer for cloud deployment.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WELCOME_CHANNEL_ID_STR = os.getenv("WELCOME_CHANNEL_ID")

# --- Essential Validation and Conversion ---

required_vars = {
    "DISCORD_TOKEN": DISCORD_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "WELCOME_CHANNEL_ID": WELCOME_CHANNEL_ID_STR,
}

# 1. Check for missing environment variables
for key, value in required_vars.items():
    if value is None:
        print(f"FATAL ERROR: Required environment variable '{key}' is missing in Render settings.")
        sys.exit(1) # Crash gracefully with an error message

# 2. Check and convert the WELCOME_CHANNEL_ID to an integer
try:
    WELCOME_CHANNEL_ID = int(WELCOME_CHANNEL_ID_STR)
except ValueError:
    print(f"FATAL ERROR: WELCOME_CHANNEL_ID '{WELCOME_CHANNEL_ID_STR}' is not a valid number. Check Render settings.")
    print("It must contain ONLY numeric digits.")
    sys.exit(1) # Crash gracefully with an error message

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Gemini Client and Personality ---
client = genai.Client(api_key=GEMINI_API_KEY)

# This System Instruction defines the bot's behavior for Gemini
ROAST_INSTRUCTION = (
    "You are a Discord Bot named 'RoastMaster-3000'. Your sole purpose is to provide "
    "lighthearted, non-offensive, and fun roasts. Your tone is witty, sarcastic, and "
    "slightly condescending, but never truly mean. Your humor should focus on generic "
    "observations about usernames, Discord etiquette, or self-deprecating bot jokes. "
    "Always keep the response short and punchy (under 15 words)."
)

GEMINI_CONFIG = genai.types.GenerateContentConfig(
    system_instruction=ROAST_INSTRUCTION,
    temperature=0.9 # High temperature for creative jokes
)

# --- Events ---

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot is ready and roasting!')

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    if channel and member.bot is False:
        user_prompt = f"Give a fun, non-offensive welcome message that includes a light roast for the new member, {member.mention}. Address them directly."
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=GEMINI_CONFIG
            )
            await channel.send(response.text)
        except Exception as e:
            # We don't crash the bot for a failed API call, just log it.
            print(f"Gemini API Error in welcome: {e}")
            await channel.send(f"Welcome, {member.mention}! My welcome system is currently down. Probably your fault.")

# --- Commands ---

@bot.command(name='roast')
async def roast_user(ctx):
    user_prompt = f"Give a quick, non-offensive roast to the user named: {ctx.author.display_name}. Focus on their username or the fact they asked for a roast."
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=GEMINI_CONFIG
        )
        await ctx.send(response.text)
    except Exception as e:
        print(f"Gemini API Error in roast: {e}")
        await ctx.send("Error: I'm too busy laughing at you to generate a roast right now.")

# --- Run the Bot ---
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    # This path should be caught by the check above, but is a final safeguard.
    print("Discord token is missing. Bot cannot start.")
    sys.exit(1)
