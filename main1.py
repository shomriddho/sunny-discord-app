import discord
from discord.ext import commands, tasks
from discord import app_commands
import itertools
from datetime import datetime, timezone, timedelta
import os 
import re 
import threading
from flask import Flask
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN') # Using token from env.txt 

# --- 1. PERSISTENT DROPDOWN LOGIC ---
class DynamicRoleDropdown(discord.ui.Select):
    def __init__(self, options_list=None):
        super().__init__(
            placeholder="Choose your roles...",
            min_values=1,
            max_values=1,
            options=options_list or [discord.SelectOption(label="Empty", value="0")],
            custom_id="persistent_role_dropdown" 
        )

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        if role_id == 0: return
        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("❌ Role not found!", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"✅ Removed: {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Added: {role.name}", ephemeral=True)

class DynamicRoleView(discord.ui.View):
    def __init__(self, options_list=None):
        super().__init__(timeout=None) 
        if options_list:
            self.add_item(DynamicRoleDropdown(options_list))

# --- 2. BOT CLASS SETUP ---
class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True 
        intents.members = True 
        super().__init__(
            command_prefix=commands.when_mentioned_or("."), 
            intents=intents, 
            help_command=None
        )

    async def setup_hook(self):
        # 1. Register persistent views
        self.add_view(DynamicRoleView()) 

        # 3. LOAD COGS (ai.py, cmds.py, etc.)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        print(f"🔍 Looking for cogs in: {current_dir}")

        for filename in os.listdir(current_dir):
            if filename.endswith('.py') and filename not in ['main1.py', '__init__.py']:
                try:
                    await self.load_extension(filename[:-3])
                    print(f"📦 Loaded Cog: {filename}")
                except Exception as e:
                    print(f"⚠️ Failed to load {filename}: {e}")

        # 4. Sync Slash Commands
        try:
            await self.tree.sync()
            print(f'📡 Synced slash commands.')
        except Exception as e:
            print(f'❌ Sync error: {e}')

    async def on_ready(self):
        print(f'✅ Logged on as {self.user}')
        if not self.change_status.is_running():
            self.change_status.start()

    @tasks.loop(seconds=20)
    async def change_status(self):
        status_list = itertools.cycle([
            discord.Game(name="Gud Bot from Dhaka 🇧🇩"),
            discord.Activity(type=discord.ActivityType.listening, name=".help"),
            discord.Game(name="Prefix: . or @mention")
        ])
        await self.change_presence(activity=next(status_list))

# --- 3. BOT INITIALIZATION ---
client = Client()

# --- 4. GLOBAL HELP UTILITY ---
def create_help_embed():
    embed = discord.Embed(
        title="🤖 Gud Bot Help Menu", 
        description="I am Gud Bot, your friendly assistant from Dhaka!",
        color=discord.Color.blue(), 
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="🛡️ Moderation", value="`.kick`, `.ban`, `.mute`, `.clear`, `.lock`", inline=False)
    embed.add_field(name="📡 Utility", value="`.ping`, `.serverinfo`, `.avatar`, `.echo` ", inline=False)
    embed.add_field(name="🧠 AI Assistant", value="`.chat <message>` or mention me!", inline=False)
    embed.add_field(name="✨ Roles", value="`.dropdownroles_create`", inline=False)
    return embed

# --- 5. SLASH COMMANDS ---
@client.tree.command(name="help", description="Show the help menu")
async def slash_help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=create_help_embed())

# --- 6. ROLE DROPDOWN COMMAND ---
@client.command(name="dropdownroles_create")
@commands.has_permissions(administrator=True)
async def prefix_dropdown_create(ctx, *, args: str):
    await ctx.message.delete()
    options = []
    role_blocks = args.split(";")
    for block in role_blocks:
        parts = block.split("|")
        if len(parts) != 3: continue
        r_id, emoji, desc = parts[0].strip(), parts[1].strip(), parts[2].strip()
        
        match = re.search(r'\d+', r_id)
        if match:
            role = ctx.guild.get_role(int(match.group()))
            if role:
                options.append(discord.SelectOption(
                    label=role.name, 
                    value=str(role.id), 
                    emoji=emoji, 
                    description=desc
                ))
    
    if options:
        view = DynamicRoleView(options)
        await ctx.send(
            embed=discord.Embed(
                title="✨ Self Roles", 
                description="Select a role below to add or remove it from yourself.", 
                color=discord.Color.blue()
            ), 
            view=view
        )

def run_flask():
    app = Flask("")

    @app.route("/")
    def home():
        return "Bot is running!"

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

if TOKEN:
    client.run(TOKEN)