import discord
from discord.ext import tasks
import datetime
import pytz
import sys
import random
import os
from google import genai
from google.genai import types


class RoastMasterCog:

    def __init__(self, client, gemini_client):
        self.client = client
        self.gemini_client = gemini_client
        
        # Conversation history per user (stores last 10 exchanges)
        self.conversation_history = {}
        self.MAX_HISTORY = 10
        
        # Configured channel ID for bot messages (fun facts, roasts, welcomes)
        # Read from environment variable BOT_CHANNEL_ID
        self.TARGET_CHANNEL_ID = int(os.environ.get('BOT_CHANNEL_ID', '0'))

        # Define the AI personality (Modify this string to change the bot's tone!)
        self.ROAST_INSTRUCTION = (
            "You are 'Sasshole', a witty Discord bot with a sharp tongue. "
            "Your responses are clever, sarcastic, and playfully mean - like a friend who teases you. "
            "Keep responses SHORT (under 20 words). Be punchy and direct. "
            "Never be actually hurtful or offensive - just playfully sassy. "
            "If asked a question, answer it with attitude. "
            "Reference previous conversations when relevant to roast harder."
        )
        self.GEMINI_CONFIG = types.GenerateContentConfig(
            system_instruction=self.ROAST_INSTRUCTION, temperature=0.9)

    async def setup(self):
        """Attaches event listeners and starts the scheduled task."""
        print("[SETUP] Registering on_message event handler...")
        sys.stdout.flush()
        
        # Store original handlers if they exist
        original_on_message = getattr(self.client, '_original_on_message', None)
        original_on_member_join = getattr(self.client, '_original_on_member_join', None)
        
        # Create wrapper functions that call our methods (named for discord.py event system)
        cog_self = self
        
        async def on_message(message):
            await cog_self.on_message(message)
        
        async def on_member_join(member):
            await cog_self.on_member_join(member)
        
        # Register events using the decorator pattern
        self.client.event(on_message)
        self.client.event(on_member_join)
        
        if not self.daily_fun_fact.is_running():
            self.daily_fun_fact.start()
        if not self.random_roast.is_running():
            self.random_roast.start()
        print("[SETUP] All event handlers registered successfully!")
        sys.stdout.flush()

    # --- Task: Daily Fun Fact (Sends to System Channel) ---

    # Set to 8:00 AM Central Time (America/Chicago)
    @tasks.loop(time=datetime.time(
        hour=8, minute=0, tzinfo=pytz.timezone('America/Chicago')))
    async def daily_fun_fact(self):
        """Sends a fun fact daily at 8:00 AM Central Time (America/Chicago)"""

        await self.client.wait_until_ready()

        channel = self.client.get_channel(self.TARGET_CHANNEL_ID)

        if not channel:
            print(f"Error: Could not find channel with ID {self.TARGET_CHANNEL_ID} for fun fact.")
            return

        fun_fact_prompt = "Share one fascinating, weird, and obscure fact that will make people go 'wait, really?'. Make it surprising and memorable. Keep it under 2 sentences."

        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash', contents=fun_fact_prompt)

            embed = discord.Embed(
                title=
                ":rotating_light: DAILY DOSE OF UTTERLY USELESS KNOWLEDGE :rotating_light:",
                description=response.text,
                color=discord.Color.gold())
            await channel.send(embed=embed)

        except Exception as e:
            print(f"Gemini API Error in daily_fun_fact: {e}")

    # --- Task: Random Roast (Every 8 hours) ---
    
    @tasks.loop(hours=24)
    async def random_roast(self):
        """Randomly picks a server member and roasts them every 8 hours"""
        
        await self.client.wait_until_ready()
        
        channel = self.client.get_channel(self.TARGET_CHANNEL_ID)
        
        if not channel:
            print(f"Error: Could not find channel with ID {self.TARGET_CHANNEL_ID} for random roast.")
            sys.stdout.flush()
            return
        
        # Get the guild from the channel
        target_guild = channel.guild
        
        # Get all non-bot members
        members = [m for m in target_guild.members if not m.bot]
        
        if not members:
            print("Error: No non-bot members found for random roast.")
            sys.stdout.flush()
            return
        
        # Pick a random member
        victim = random.choice(members)
        
        print(f"[RANDOM ROAST] Selected victim: {victim.display_name}")
        sys.stdout.flush()
        
        roast_prompt = "Write a quick, witty roast that pokes fun at everyday things like being online too much, coffee addiction, or procrastination. Be clever and sarcastic. Under 25 words. No greeting or name - just the roast."
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=roast_prompt,
                config=self.GEMINI_CONFIG
            )
            
            await channel.send(f"Hey {victim.mention}! {response.text}")
            print(f"[RANDOM ROAST] Sent roast to {victim.display_name}")
            sys.stdout.flush()
            
        except Exception as e:
            print(f"Gemini API Error in random_roast: {e}")
            sys.stdout.flush()

    @random_roast.before_loop
    async def before_random_roast(self):
        """Wait until the bot is ready before starting the random roast loop"""
        await self.client.wait_until_ready()

    # --- Event Handler: Mentions and Replies ---

    def get_conversation_history(self, user_id):
        """Get conversation history for a user, or create empty list"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        return self.conversation_history[user_id]
    
    def add_to_history(self, user_id, user_msg, bot_msg):
        """Add an exchange to user's conversation history"""
        history = self.get_conversation_history(user_id)
        history.append({"user": user_msg, "bot": bot_msg})
        # Keep only last MAX_HISTORY exchanges
        if len(history) > self.MAX_HISTORY:
            self.conversation_history[user_id] = history[-self.MAX_HISTORY:]
    
    def format_history_for_prompt(self, user_id):
        """Format conversation history as context for the prompt"""
        history = self.get_conversation_history(user_id)
        if not history:
            return ""
        
        context = "\n\nPrevious conversation with this user:\n"
        for exchange in history[-5:]:  # Last 5 exchanges for context
            context += f"User: {exchange['user']}\n"
            context += f"You: {exchange['bot']}\n"
        return context

    async def on_message(self, message):
        # 1. Ignore messages from the bot itself
        if message.author == self.client.user:
            return

        # Debug logging
        print(f"[MESSAGE] From {message.author}: {message.content}")
        sys.stdout.flush()

        # 2. Check for Direct Mention OR Reply to the Bot
        is_mention = self.client.user.mentioned_in(message)
        is_reply_to_bot = (message.reference and message.reference.resolved
                           and message.reference.resolved.author
                           == self.client.user)

        print(
            f"[MESSAGE] is_mention={is_mention}, is_reply_to_bot={is_reply_to_bot}"
        )
        sys.stdout.flush()

        if is_mention or is_reply_to_bot:

            target_user = message.author
            user_id = target_user.id
            
            # Get conversation history context
            history_context = self.format_history_for_prompt(user_id)

            # Determine the specific prompt for Gemini
            if is_mention:
                prompt_text = f"{target_user.display_name} said: '{message.content}'\n\nGive a witty, sarcastic comeback. Be clever and playfully mean. Keep it short and punchy.{history_context}"

            elif is_reply_to_bot:
                original_bot_message = message.reference.resolved.content
                prompt_text = f"You previously said: '{original_bot_message}'\n{target_user.display_name} replied: '{message.content}'\n\nClap back with a clever retort. Stay sassy and reference what was said.{history_context}"
            else:
                return  # Should not happen

            # Generate and send response
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_text,
                    config=self.GEMINI_CONFIG)

                bot_response = response.text
                
                # Store this exchange in history
                self.add_to_history(user_id, message.content, bot_response)
                
                # Responds in the channel the message came from
                await message.reply(bot_response, mention_author=True)

            except Exception as e:
                print(f"Gemini API Error in on_message: {e}")
                await message.channel.send(
                    "Error: My witty circuits are currently fried. Try talking to a human."
                )

    # --- Event Handler: New Member Welcome (Sends to System Channel) ---

    async def on_member_join(self, member):
        channel = self.client.get_channel(self.TARGET_CHANNEL_ID)

        if channel and not member.bot:
            user_prompt = f"Welcome the new member {member.display_name} with a sassy one-liner that's funny but not mean. Make them feel roasted AND welcomed. Under 20 words."

            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config=self.GEMINI_CONFIG)
                await channel.send(response.text)
            except Exception as e:
                print(f"Gemini API Error in welcome: {e}")
                await channel.send(
                    f"Welcome, {member.mention}! My welcome system had a meltdown. Stop breaking my code."
                )
