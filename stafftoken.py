import discord
from discord import app_commands
from discord.ext import commands
import secrets, time, base64, os, json, io, random
from PIL import Image, ImageDraw
from datetime import datetime

TOKEN_FILE = "tokens.json"
CONFIG_FILE = "config.json"

class StaffSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.otp_store = self.load_json(TOKEN_FILE)
        self.config = self.load_json(CONFIG_FILE, default={"staff_roles": [], "log_channel": None})
        self.security_logs = {} # {user_id: {"count": 0, "timeout_until": 0.0, "hard_locked": False}}
        self.active_captchas = {}

    def load_json(self, filename, default=None):
        if os.path.exists(filename):
            with open(filename, "r") as f: return json.load(f)
        return default if default is not None else {}

    def save_json(self, filename, data):
        with open(filename, "w") as f: json.dump(data, f, indent=4)

    def generate_token(self, user_id):
        p1 = base64.b64encode(str(user_id).encode()).decode().rstrip("=")
        p2 = base64.b64encode(str(int(time.time())).encode()).decode().rstrip("=")
        p3 = secrets.token_urlsafe(32)
        return f"{p1}.{p2}.{p3}"

    def create_captcha(self, text):
        img = Image.new('RGB', (150, 60), color=(35, 39, 42))
        d = ImageDraw.Draw(img)
        for _ in range(10):
            d.line([(random.randint(0, 150), random.randint(0, 60)), (random.randint(0, 150), random.randint(0, 60))], fill=(114, 137, 218), width=1)
        d.text((55, 22), text, fill=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf

    async def log_event(self, interaction, message, critical=False):
        cid = self.config.get("log_channel")
        if cid:
            channel = interaction.guild.get_channel(cid)
            if channel:
                embed = discord.Embed(title="🛡️ Security", description=message, color=discord.Color.red() if critical else discord.Color.orange())
                await channel.send(embed=embed)

    # --- COMMANDS ---

    @app_commands.command(name="redeem")
    async def redeem(self, interaction: discord.Interaction, token: str, captcha_answer: str = None):
        uid = interaction.user.id
        now = time.time()
        log = self.security_logs.setdefault(uid, {"count": 0, "timeout_until": 0.0, "hard_locked": False})

        if log["hard_locked"]:
            return await interaction.response.send_message("❌ **LOCKED.** Contact Owner.", ephemeral=True)
        
        if now < log["timeout_until"]:
            rem = int(log["timeout_until"] - now)
            return await interaction.response.send_message(f"⏳ Wait {rem}s.", ephemeral=True)

        if log["count"] >= 5:
            if not captcha_answer or captcha_answer != self.active_captchas.get(uid):
                code = str(random.randint(1000, 9999))
                self.active_captchas[uid] = code
                return await interaction.response.send_message("⚠️ Solve captcha:", file=discord.File(self.create_captcha(code), "captcha.png"), ephemeral=True)

        if token in self.otp_store and self.otp_store[token] == uid:
            roles = [interaction.guild.get_role(rid) for rid in self.config["staff_roles"] if interaction.guild.get_role(rid)]
            await interaction.user.add_roles(*roles)
            del self.otp_store[token]
            self.save_json(TOKEN_FILE, self.otp_store)
            self.security_logs[uid] = {"count": 0, "timeout_until": 0.0, "hard_locked": False}
            await interaction.response.send_message("🔓 Success.", ephemeral=True)
        else:
            log["count"] += 1
            c = log["count"]
            if c >= 15: log["hard_locked"] = True
            elif c >= 10: log["timeout_until"] = now + 3600
            elif c >= 7: log["timeout_until"] = now + 900
            
            await self.log_event(interaction, f"{interaction.user.name} failed token ({c}/15)", critical=(c >= 15))
            await interaction.response.send_message(f"❌ Invalid. Fail count: {c}", ephemeral=True)

    @app_commands.command(name="gentoken")
    @commands.is_owner()
    async def gentoken(self, interaction: discord.Interaction, target: discord.Member):
        t = self.generate_token(target.id)
        self.otp_store[t] = target.id
        self.save_json(TOKEN_FILE, self.otp_store)
        await interaction.response.send_message(f"Token for {target.name}: `{t}`", ephemeral=True)

    @app_commands.command(name="token_wrong_reset")
    @app_commands.checks.has_permissions(administrator=True)
    async def reset(self, interaction: discord.Interaction, target: discord.Member):
        self.security_logs[target.id] = {"count": 0, "timeout_until": 0.0, "hard_locked": False}
        await interaction.response.send_message(f"✅ Reset {target.name}.", ephemeral=True)

    @app_commands.command(name="staffrole_add")
    async def s_add(self, interaction: discord.Interaction, role: discord.Role):
        if interaction.user.id != interaction.guild.owner_id: return
        self.config["staff_roles"].append(role.id)
        self.save_json(CONFIG_FILE, self.config)
        await interaction.response.send_message(f"Added {role.name}", ephemeral=True)

    @app_commands.command(name="set_logs")
    async def s_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.user.id != interaction.guild.owner_id: return
        self.config["log_channel"] = channel.id
        self.save_json(CONFIG_FILE, self.config)
        await interaction.response.send_message(f"Logs -> {channel.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StaffSystem(bot))