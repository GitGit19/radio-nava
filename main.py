import discord
from discord.ext import commands
import os
import asyncio

# ۱. تنظیمات دسترسی‌ها
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ۲. 🆔 آی‌دی دیسکورد خودم
OWNER_ID = 350787863241031681

current_index = 0

# ۳. کلاس کنترل دکمه‌ها
class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی به کنسول استودیو محدود است.", ephemeral=True)
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
        await interaction.response.send_message("📻 پخش برنامه متوقف شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی به کنسول استودیو محدود است.", ephemeral=True)
            return
        self.vc.stop()
        await interaction.response.send_message("⏩ در حال پخش ترانه بعدی...", ephemeral=True)

# ۴. منطق پخش و وضعیت (Status) جدید
async def play_logic(ctx, vc):
    global current_index
    # مرتب‌سازی دقیق فایل‌ها (1, 2, 3...)
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')],
                   key=lambda x: int(x.replace('nava', '').replace('.mp3', '') or 0))
    
    if not songs:
        await ctx.send("❌ آرشیو پیدا نشد!")
        return

    view = RadioControl(vc, songs)
    while vc.is_connected():
        song_file = songs[current_index]
        
        # 🎙️ استخراج دقیق عدد از نام فایل (مثلاً nava13 -> 13)
        song_num = song_file.replace('nava', '').replace('.mp3', '')
        friendly_name = f"ترانه-{song_num}"
        
        # ✨ اصلاح وضعیت: در حال پخش ترانه-۱۳
        status_text = f"در حال پخش {friendly_name}"
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, 
                name=status_text
            )
        )

        embed = discord.Embed(
            title="📻 رادیو ۲۴ ساعته‌ی نَــــوا", 
            description=f"🎵 **در حال پخش:** `{friendly_name}`\n🎙️ *پخش زنده از استودیو مرکزی*", 
            color=0x9b59b6
        )
        await ctx.send(embed=embed, view=view)
        
        vc.play(discord.FFmpegPCMAudio(song_file))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# شناسه کانال صوتی مخصوص رادیو نَــــوا
RADIO_CHANNEL_ID = 524824235709825045  # <--- آی‌دی کانال رادیو 

# ۵. دستور شروع پخش
@bot.command(name="play")
async def start_radio(ctx):
    # ۱. چک کردن دسترسی شما
    if ctx.author.id != OWNER_ID:
        await ctx.send(f"❌ {ctx.author.mention}، رادیو نَــــوا فقط از استودیو روشن می‌شود.")
        return

    # ۲. پیدا کردن کانال مخصوص رادیو
    channel = bot.get_channel(RADIO_CHANNEL_ID)
    
    if channel is None:
        await ctx.send("❌ کانال رادیو پیدا نشد! لطفا ID کانال را در کد چک کنید.")
        return

    # ۳. اتصال مستقیم به کانال (چه شما آنجا باشید چه نباشید)
    try:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            
        vc = await channel.connect()
        await ctx.send(f"📡 **اتصال برقرار شد.** رادیو نَــــوا در کانال `{channel.name}` پخش برنامه‌های خود را آغاز کرد.")
        await play_logic(ctx, vc)
        
    except Exception as e:
        await ctx.send(f"❌ خطا در برقراری اتصال استودیو: {e}")
        
bot.run(os.getenv('DISCORD_TOKEN'))
