import discord
from discord.ext import tasks
import datetime
import pytz

class RoastMasterCog:
    def __init__(self, client, gemini_client):
        self.client = client
        self.gemini_client = gemini_client
        
        # Define the AI personality
        self.ROAST_INSTRUCTION = (
            "You are a Discord Bot named 'RoastMaster-3000'. Your sole purpose is to provide "
            "crisp, funny, mean, but non-offensive responses. Your tone is witty, sarcastic, and "
            "mildly condescending. Your humor should focus on generic observations. "
            "Always keep the response short and punchy (under 15 words)."
        )
        self.GEMINI_CONFIG = self.gemini_client.types.GenerateContentConfig(
            system_instruction=self.ROAST_INSTRUCTION,
            temperature=0.9
        )
        
    async def setup(self):
        """Attaches event listeners and starts the scheduled task."""
        # Manually attach event listeners from this class to the client
        self.client.event(self.on_message)
        self.client.event(self.on_member_join)
        
        # Start the daily fun fact task
        self.daily_fun_fact.start()

    # --- Task: Daily Fun Fact (Sends to System Channel) ---
    
    @tasks.loop(time=datetime.time(hour=8, minute=0, tzinfo=pytz.timezone('America/Chicago')))
    async def daily_fun_fact(self):
        """Sends a fun fact daily at 8:00 AM Central Time (America/Chicago)"""
        
        await self.client.wait_until_ready()
        
        # Find the first guild (server) the bot is in and use its system channel
        target_guild = self.client.guilds[0] if self.client.guilds else None
        channel = target_guild.system_channel if target_guild else None

        if not channel:
            print(f"Error: Could not find a system channel for the fun fact.")
            return

        print(f"Generating and sending daily fun fact to {channel.name}...")
        
        fun_fact_prompt = "Generate one short, extremely interesting, and obscure fun fact."
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=fun_fact_prompt
            )
            
            embed = discord.Embed(
                title=":rotating_light: DAILY DOSE OF UTTERLY USELESS KNOWLEDGE :rotating_light:",
                description=response.text,
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Gemini API Error in daily_fun_fact: {e}")

    # --- Event Handler: Mentions and Replies (Works in all channels) ---

    async def on_message(self, message):
        # 1. Ignore messages from the bot itself
        if message.author == self.client.user:
            return

        # 2. Check for Direct Mention OR Reply to the Bot
        is_mention = self.client.user.mentioned_in(message)
        is_reply_to_bot = (
            message.reference and 
            message.reference.resolved and 
            message.reference.resolved.author == self.client.user
        )

        if is_mention or is_reply_to_bot:
            
            target_user = message.author
            
            # Determine the specific prompt for Gemini
            if is_mention:
                prompt_text = f"The user, {target_user.display_name}, mentioned you directly. Give a crisp, funny, mean, non-offensive response to their message: '{message.content}'"
            
            elif is_reply_to_bot:
                original_bot_message = message.reference.resolved.content 
                prompt_text = f"The user, {target_user.display_name}, is replying to your previous message, '{original_bot_message}'. Give a funny, mean, non-offensive retort to their new message: '{message.content}'"
            
            # Generate and send response
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_text,
                    config=self.GEMINI_CONFIG
                )
                
                # Responds in the channel the message came from
                await message.reply(response.text, mention_author=True)
                
            except Exception as e:
                print(f"Gemini API Error in on_message: {e}")
                await message.channel.send("Error: My witty circuits are currently fried. Try talking to a human.")


    # --- Event Handler: New Member Welcome (Sends to System Channel) ---

    async def on_member_join(self, member):
        # Find the server's designated system channel
        channel = member.guild.system_channel

        if channel and not member.bot:
            print(f"New member {member.display_name} joined. Roasting to system channel.")
            
            user_prompt = f"Give a savage, fun, non-offensive welcome message that includes a light roast for the new member, {member.mention}. Address them directly. Keep it very short."
            
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config=self.GEMINI_CONFIG
                )
                await channel.send(response.text)
            except Exception as e:
                print(f"Gemini API Error in welcome: {e}")
                await channel.send(f"Welcome, {member.mention}! My welcome system had a meltdown. Stop breaking my code.")
