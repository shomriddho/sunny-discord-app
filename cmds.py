import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta

class Cmds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx):
        await ctx.send(f'🏓 {round(self.bot.latency * 1000)}ms')

    @commands.hybrid_command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🗑️ Deleted {amount} messages.", delete_after=3)

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        await member.kick(reason=reason)
        await ctx.send(f'✅ **{member.name}** has been kicked.')

    @commands.hybrid_command(name="echo")
    @commands.has_permissions(manage_messages=True)
    async def echo(self, ctx, *, message: str):
        if not ctx.interaction: await ctx.message.delete()
        embed = discord.Embed(description=message, color=discord.Color.blue(), timestamp=datetime.now(timezone.utc))
        embed.set_author(name="Gud Bot Announcement", icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

@commands.hybrid_command(name="help", description="Show the help menu")
async def help(self, ctx):
        # This tells the bot to use the helper function from the mother file
        # or you can define the embed directly here
        embed = discord.Embed(
            title="🤖 Gud Bot Help Menu", 
            description="I am your friendly assistant from Dhaka!",
            color=discord.Color.blue()
        )
        embed.add_field(name="🧠 AI", value="`.chat` or `/chat`", inline=True)
        embed.add_field(name="🛡️ Mod", value="`.kick`, `.clear`", inline=True)
        embed.set_footer(text="Use prefix '.' or mention me!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Cmds(bot))