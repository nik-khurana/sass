import discord
from discord.ext import commands, tasks
import datetime
import pytz

class RoastMasterCog(commands.Cog):
    def __init__(self, bot, gemini_client, welcome_channel_id):
        self.bot = bot
        self.client = gemini_client
        self.welcome_channel_id = welcome_channel_id
        
        # Define the AI personality
        self.ROAST_INSTRUCTION = (
            "You are a Discord Bot named 'Sasshole'. Your sole purpose is to provide "
            "crisp, funny, mean, but non-offensive responses. Your tone is witty, sarcastic, and "
            "mildly condescending. Your humor should focus on generic observations. "
            "Always keep the response short and punchy (under 15 words)."
        )
        self.GEMINI_CONFIG = self.client.types.GenerateContentConfig(
            system_instruction=self.ROAST_INSTRUCTION,
            temperature=0.9
        )
        
        # Start the daily fun fact task
        self.daily_fun_fact.start()

    def cog_unload(self):
        # Stop the task when the cog is unloaded
        self.daily_fun_fact.cancel()

    # --- Task: Daily Fun Fact ---
    
    @tasks.loop(time=datetime.time(hour=8, minute=0, tzinfo=pytz.timezone('America/Chicago')))
    async def daily_fun_fact(self):
        """Sends a fun fact daily at 8:00 AM Central Time (America/Chicago)"""
        channel = self.bot.get_channel(self.welcome_channel_id)
        if not channel:
            print(f"Error: Fun fact channel {self.welcome_channel_id} not found.")
            return

        print("Generating and sending daily fun fact...")
        
        fun_fact_prompt = "Generate one short, extremely interesting, and obscure fun fact."
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=fun_fact_prompt
            )
            # Send the fun fact as an embed for visual appeal
            embed = discord.Embed(
                title=":rotating_light: DAILY DOSE OF UTTERLY USELESS KNOWLEDGE :rotating_light:",
                description=response.text,
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Gemini API Error in daily_fun_fact: {e}")

    # --- Event Handler: Mentions and Replies ---

    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. Ignore bot messages
        if message.author.bot:
            return

        # 2. Check for Direct Mention OR Reply to the Bot
        is_mention = self.bot.user.mentioned_in(message)
        is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author == self.bot.user

        if is_mention or is_reply_to_bot:
            
            # Use the mention or the original message's author for the reply
            target_user = message.author
            
            # Determine the prompt type based on interaction
            if is_mention:
                print(f"Received direct mention from {target_user.display_name}")
                prompt_text = f"The user, {target_user.display_name}, mentioned you directly. Give a crisp, funny, mean, non-offensive response to their message: '{message.content}'"
            elif is_reply_to_bot:
                print(f"Received reply to a bot message from {target_user.display_name}")
                # You can access the message the user is replying to here:
                original_bot_message = message.reference.resolved.content 
                prompt_text = f"The user, {target_user.display_name}, is replying to your previous message, '{original_bot_message}'. Give a funny, mean, non-offensive retort to their new message: '{message.content}'"
            
            else:
                return # Should not happen, but safe check

            # Generate response using Gemini
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt_text,
                    config=self.GEMINI_CONFIG
                )
                
                # Reply directly to the user's message, which handles the reply chain automatically
                await message.reply(response.text, mention_author=True)
                
            except Exception as e:
                print(f"Gemini API Error in on_message: {e}")
                await message.channel.send("Error: My witty circuits are currently fried. Try talking to a human.")

    # --- Event Handler: New Member Welcome ---

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(self.welcome_channel_id)

        if channel and not member.bot:
            print(f"New member {member.display_name} joined. Roasting...")
            
            user_prompt = f"Give a savage, fun, non-offensive welcome message that includes a light roast for the new member, {member.mention}. Address them directly. Keep it very short."
            
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_prompt,
                    config=self.GEMINI_CONFIG
                )
                await channel.send(response.text)
            except Exception as e:
                print(f"Gemini API Error in welcome: {e}")
                await channel.send(f"Welcome, {member.mention}! My welcome system had a meltdown. Stop breaking my code.")
