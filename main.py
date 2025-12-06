import discord
from discord.ext import commands
from google import genai
import os

# --- Configuration & Setup ---

# The environment variables will be set later on the Render hosting platform
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Required Intents for commands and member join events
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Gemini Client and Personality ---
client = genai.Client(api_key=GEMINI_API_KEY)

# This System Instruction defines the bot's behavior for Gemini
ROAST_INSTRUCTION = (
    "You are a Discord Bot named 'Sasshole'. Your sole purpose is to provide "
    "lighthearted, non-offensive, and fun roasts. Your tone is witty, sarcastic, and "
    "slightly condescending, but never truly mean. Your humor should focus on generic "
    "observations about usernames, Discord etiquette, or self-deprecating bot jokes. "
    "Always keep the response short and punchy (under 20 words)."
)

GEMINI_CONFIG = genai.types.GenerateContentConfig(
    system_instruction=ROAST_INSTRUCTION,
    temperature=0.9  # High temperature for creative jokes
)


# --- Events ---

# 1. Confirmation when the bot starts
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot is ready and roasting!')


# 2. Welcome and Roast New Members
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    if channel and member.bot is False:  # Ignore other bots joining
        user_prompt = f"Give a fun, non-offensive welcome message that includes a light roast for the new member, {member.mention}. Address them directly."
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=GEMINI_CONFIG
            )
            await channel.send(response.text)
        except Exception as e:
            print(f"Gemini API Error in welcome: {e}")
            await channel.send(f"Welcome, {member.mention}! My welcome system is currently down. Probably your fault.")


# --- Commands ---

# 3. Roast Command: !roast
@bot.command(name='roast')
async def roast_user(ctx):
    # Contextual prompt for the model
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
bot.run(DISCORD_TOKEN)