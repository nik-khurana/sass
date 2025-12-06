import discord
from discord.ext import commands
from google import genai
import os
import sys

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

# --- 2. Discord Bot Setup (Intents) ---

intents = discord.Intents.default()
# PRIVILEGED INTENTS (MUST be enabled in Discord Developer Portal)
intents.members = True          # Required for on_member_join
intents.message_content = True  # CRITICAL: Required to read command and mention text

bot = commands.Bot(command_prefix='!', intents=intents)

# --- 3. Gemini Client and Personality ---

client = genai.Client(api_key=GEMINI_API_KEY)

ROAST_INSTRUCTION = (
    "You are a Discord Bot named 'Sasshole'. Your sole purpose is to provide "
    "lighthearted, non-offensive, fun, and clever roasts. Your tone is witty, "
    "sarcastic, and mildly condescending, but never cruel. Your humor should focus on "
    "generic observations. Always keep the response short and punchy (under 15 words)."
)

GEMINI_CONFIG = genai.types.GenerateContentConfig(
    system_instruction=ROAST_INSTRUCTION,
    temperature=0.9
)

# --- 4. Core Roast Function (Used by both Command and Mention) ---

async def generate_and_send_roast(ctx_or_message, target_user, prompt_type="command"):
    if prompt_type == "mention":
        user_prompt = f"Give a quick, non-offensive roast to the user named: {target_user.display_name} who mentioned you directly. Focus on their audacity."
    else: # command
        user_prompt = f"Give a quick, non-offensive roast to the user named: {target_user.display_name}. Focus on their username or the fact they asked for a roast."

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=GEMINI_CONFIG
        )
        await ctx_or_message.channel.send(f"{target_user.mention} {response.text}")
    except Exception as e:
        print(f"Gemini API Error in roast: {e}")
        await ctx_or_message.channel.send("Error: My witty servers just went down. Don't worry, it's not you. (It's definitely you.)")

# --- 5. Event Handlers ---

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Bot is ready and roasting!')

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    if channel and member.bot is False:
        user_prompt = f"Give a savage, fun, non-offensive welcome message that includes a light roast for the new member, {member.mention}. Address them directly. Keep it very short."
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=GEMINI_CONFIG
            )
            await channel.send(response.text)
        except Exception as e:
            print(f"Gemini API Error in welcome: {e}")
            await channel.send(f"Welcome, {member.mention}! My welcome system had a meltdown. Stop breaking my code.")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check for direct bot mention
    if bot.user.mentioned_in(message):
        # Only respond if the message starts with a mention of the bot
        if message.content.startswith(f'<@{bot.user.id}>') or message.content.startswith(f'<@!{bot.user.id}>'):
            print(f"Received direct mention from {message.author.display_name}")
            # Call the core function with the message object
            await generate_and_send_roast(message, message.author, "mention")
            return # Stop processing after responding to mention

    # Process traditional commands (like !roast) after checking for mentions
    await bot.process_commands(message)

# --- 6. The Traditional Command (Kept for !roast) ---

# Note: The actual logic is now in generate_and_send_roast
@bot.command(name='roast')
async def roast_user(ctx):
    print(f"Received !roast command from {ctx.author.display_name}") 
    await generate_and_send_roast(ctx, ctx.author, "command")

# --- 7. Run the Bot ---
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("Discord token is missing. Bot cannot start.")
    sys.exit(1)
