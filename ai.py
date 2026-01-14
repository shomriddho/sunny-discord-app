import discord
from discord.ext import commands
import google.generativeai as genai
import os

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {} 
        
        # 1. Force 'rest' to avoid v1beta redirection bugs
        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY"),
            transport='rest'
        )
        
        # 2. Use the 2.5-flash model which is the 2026 free standard
        # 'gemini-1.5-flash' is now considered a 'legacy' model for many accounts.
        try:
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash', 
                system_instruction="You are Gud Bot from Dhaka. Keep it warm and short."
            )
            print("✅ AI System Online: Using Gemini 2.5 Flash")
        except Exception as e:
            print(f"❌ Initialization Error: {e}")

    @commands.hybrid_command(name="chat")
    async def chat(self, ctx, *, message: str):
        if not hasattr(self, 'model'):
            return await ctx.reply("❌ AI failed to load. Please check the terminal.")

        user_id = ctx.author.id
        if user_id not in self.conversations:
            self.conversations[user_id] = self.model.start_chat(history=[])

        if ctx.interaction:
            await ctx.defer()

        try:
            response = self.conversations[user_id].send_message(message)
            await ctx.reply(response.text)
        except Exception as e:
            # Handle that pesky 429 quota error if it pops up
            if "429" in str(e):
                await ctx.reply("⚠️ **Quota Limit:** Google is throttling the free tier. Try again in 60 seconds.")
            else:
                await ctx.reply(f"❌ AI Error: {e}")

async def setup(bot):
    await bot.add_cog(AI(bot))