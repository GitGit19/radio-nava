import discord
from discord.ext import commands
import os
import asyncio

# ۱. تنظیمات دسترسی‌های بات
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ۲. 🆔 آی‌دی دیسکورد خودت را اینجا وارد کن (بسیار مهم)
OWNER_ID = 123456789012345678 

current_index = 0

# ۳. کلاس کنترل رادیو (دکمه‌های ضبط‌صوت)
class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ شما اجازه کنترل رادیو را ندارید.", ephemeral=True)
            return
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ بازگشت به ترانه قبلی", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ فقط مدیر اصلی می‌تواند رادیو را خاموش کند.", ephemeral=True)
            return
        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        await interaction.response.send_message("📻 رادیو نـــــوا خاموش شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ شما اجازه کنترل رادیو را ندارید.", ephemeral=True)
            return
        self.vc.stop()
        await interaction.response.send_message("⏩ ترانه بعدی", ephemeral=True)

# ۴. منطق پخش خودکار و وضعیت پروفایل
async def play_logic(ctx, vc):
    global current_index
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')])
    
    if not songs:
        await ctx.send("❌ هیچ فایل صوتی پیدا نشد!")
        return

    view = RadioControl(vc, songs)
    while vc.is_connected():
        song = songs[current_index]
        
        # نمایش نام آهنگ در وضعیت (Status) پروفایل بات
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, 
                name=f"نـــــوا: {song}"
            )
        )

        embed = discord.Embed(
            title="📻 رادیو ۲۴ ساعته‌ی نـــــوا", 
            description=f"🎵 در حال پخش: `{song}`\n🆔 کنترل فقط توسط مدیر اصلی", 
            color=0x9b59b6
        )
        await ctx.send(embed=embed, view=view)
        
        vc.play(discord.FFmpegPCMAudio(song))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# ۵. دستور شروع پخش (محدود به آی‌دی شما)
@bot.command(name="play", aliases=["start", "nava"])
async def start_radio(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send(f"❌ {ctx.author.mention}، فقط مدیر اصلی اجازه روشن کردن رادیو را دارد.")
        return

    if ctx.author.voice:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        vc = await ctx.author.voice.channel.connect()
        await play_logic(ctx, vc)
    else:
        await ctx.send("❌ ابتدا وارد یک کانال صوتی شوید!")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} آنلاین شد. رادیو نـــــوا آماده به کار است.')

# ۶. اجرای بات با توکن مخفی
bot.run(os.getenv('DISCORD_TOKEN'))
