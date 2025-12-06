import discord
from discord.ext import tasks
import datetime
import pytz
import sys
import random
from google import genai
from google.genai import types


class RoastMasterCog:

    def __init__(self, client, gemini_client):
        self.client = client
        self.gemini_client = gemini_client
        
        # Conversation history per user (stores last 10 exchanges)
        self.conversation_history = {}
        self.MAX_HISTORY = 10

        # Define the AI personality (Modify this string to change the bot's tone!)
        self.ROAST_INSTRUCTION = (
            "You are a Discord Bot named 'Sasshole'. Your sole purpose is to provide "
            "crisp, funny, mean, but non-offensive responses. Your tone is witty, sarcastic, and "
            "mildly condescending. Your humor should focus on generic observations. "
            "Always keep the response short and punchy (under 15 words). Answer the questions if asked by a user. "
            "You remember previous conversations with users and can reference them."
            "Be Nice sometimes too."
            "answer the questions if asked by a user."
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

        target_guild = self.client.guilds[0] if self.client.guilds else None
        channel = target_guild.system_channel if target_guild else None

        if not channel:
            print(f"Error: Could not find a system channel for the fun fact.")
            return

        fun_fact_prompt = "Generate one short, extremely interesting, and obscure fun fact."

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
    
    @tasks.loop(hours=8)
    async def random_roast(self):
        """Randomly picks a server member and roasts them every 8 hours"""
        
        await self.client.wait_until_ready()
        
        target_guild = self.client.guilds[0] if self.client.guilds else None
        channel = target_guild.system_channel if target_guild else None
        
        if not channel:
            print(f"Error: Could not find a system channel for random roast.")
            sys.stdout.flush()
            return
        
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
        
        roast_prompt = f"Generate a funny, playful, non-offensive roast. Make it witty and sarcastic but keep it light-hearted. Keep it under 30 words. Don't be mean about appearance or personal traits. Do NOT include any name or greeting - just the roast itself."
        
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
                prompt_text = f"The user, {target_user.display_name}, mentioned you directly. Give a crisp, funny, mean, non-offensive response to their message: '{message.content}'{history_context}"

            elif is_reply_to_bot:
                original_bot_message = message.reference.resolved.content
                prompt_text = f"The user, {target_user.display_name}, is replying to your previous message, '{original_bot_message}'. Give a funny, mean, non-offensive retort to their new message: '{message.content}'{history_context}"
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
        channel = member.guild.system_channel

        if channel and not member.bot:
            user_prompt = f"Give a savage, fun, non-offensive welcome message that includes a light roast for the new member, {member.mention}. Address them directly. Keep it very short."

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
