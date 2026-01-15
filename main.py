import discord
from discord.ext import commands
import os
import asyncio

# ۱. تنظیمات دسترسی‌های بات
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ۲. 🆔 آی‌دی دیسکورد خوم
OWNER_ID = 350787863241031681

current_index = 0

# ۳. کلاس کنترل رادیو (دکمه‌های کنسول استودیو)
class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی به کنسول مدیریت استودیو محدود است.", ephemeral=True)
            return
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ در حال بازگشت به آرشیو قبلی...", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ فقط اپراتور استودیو اجازه قطع پخش را دارد.", ephemeral=True)
            return
        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        await interaction.response.send_message("📻 پخش برنامه از استودیو متوقف شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی به کنسول مدیریت استودیو محدود است.", ephemeral=True)
            return
        self.vc.stop()
        await interaction.response.send_message("⏩ در حال پخش ترانه بعدی از لیست استودیو...", ephemeral=True)

# ۴. منطق پخش و وضعیت پروفایل
async def play_logic(ctx, vc):
    global current_index
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')])
    
    if not songs:
        await ctx.send("❌ آرشیو موسیقی در استودیو پیدا نشد!")
        return

    view = RadioControl(vc, songs)
    while vc.is_connected():
        song = songs[current_index]
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"نـــــوا: {song}"))

        embed = discord.Embed(
            title="📻 رادیو ۲۴ ساعته‌ی نـــــوا", 
            description=f"🎵 **در حال پخش:** `{song}`\n🎙️ *پخش زنده از استودیو مرکزی*", 
            color=0x9b59b6
        )
        await ctx.send(embed=embed, view=view)
        
        vc.play(discord.FFmpegPCMAudio(song))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# ۵. دستور شروع پخش (محدود به آی‌دی خودم با پیام جدید)
@bot.command(name="play", aliases=["start", "nava"])
async def start_radio(ctx):
    if ctx.author.id != OWNER_ID:
        # پیام اختصاصی من:
        await ctx.send(f"❌ {ctx.author.mention}، رادیو نوا فقط از استودیو روشن می‌شود.")
        return

    if ctx.author.voice:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        vc = await ctx.author.voice.channel.connect()
        await play_logic(ctx, vc)
    else:
        await ctx.send("❌ ابتدا باید وارد یک کانال صوتی شوید!")

@bot.event
async def on_ready():
    print(f'✅ Voices for the One (نوا) آماده پخش از استودیو است.')

# ۶. اجرای بات
bot.run(os.getenv('DISCORD_TOKEN'))
