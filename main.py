import discord
from discord.ext import commands
import os
import asyncio
import re

# ۱. تنظیمات دسترسی‌ها
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# ۲. 🆔 تنظیمات اختصاصی 
OWNER_ID = 350787863241031681  # آی‌دی دیسکورد من
RADIO_CHANNEL_ID = 524824235709825045  # آی‌دی کانال رادیو نَــــوا

current_index = 0
active_vc = None

def extract_number(filename):
    match = re.search(r'nava(\d+)', filename)
    return int(match.group(1)) if match else 0

# ۳. کنسول مدیریت
class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی محدود.", ephemeral=True)
            return
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ ترانه قبلی", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی محدود.", ephemeral=True)
            return
        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        try: await interaction.guild.me.edit(nick="Radio Nava")
        except: pass
        await interaction.response.send_message("📻 استودیو خاموش شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی محدود.", ephemeral=True)
            return
        self.vc.stop()
        await interaction.response.send_message("⏩ ترانه بعدی", ephemeral=True)

# ۴. منطق پخش و نمایش در کانال صوتی
async def play_logic(vc):
    global current_index, active_vc
    active_vc = vc
    
    # ۱. تثبیت نام بات روی Radio Nava برای Sidebar
    try:
        await vc.guild.me.edit(nick="Radio Nava")
    except Exception as e:
        print(f"خطا در تنظیم نام: {e}")

    while vc.is_connected():
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        
        if not songs: break
            
        song_file = songs[current_index % len(songs)]
        song_num = extract_number(song_file)
        # متنی که دقیقاً در عکس‌های شما بود
        display_text = f"در حال پخش ترانه-{song_num}"
        
        # ۲. تنظیم وضعیت (Status)
        # این متن در Sidebar زیر "Radio Nava" و در کانال صوتی زیر نام بات قرار می‌گیرد
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening, 
                name=display_text
            )
        )

        # پخش صدا
        vc.play(discord.FFmpegPCMAudio(song_file))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# ۵. دستورات
@bot.command(name="play")
async def start_radio(ctx):
    if ctx.author.id != OWNER_ID: return
    channel = bot.get_channel(RADIO_CHANNEL_ID)
    if channel:
        if ctx.voice_client: await ctx.voice_client.disconnect()
        vc = await channel.connect()
        await ctx.send("📡 رادیو روشن شد. برای کنترل: `!display`", delete_after=5)
        await play_logic(vc)

@bot.command(name="display")
async def display_status(ctx):
    global active_vc
    if active_vc and active_vc.is_connected():
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        song_num = extract_number(songs[current_index % len(songs)])
        
        view = RadioControl(active_vc, songs)
        embed = discord.Embed(
            title="📻 رادیو ۲۴ ساعته‌ی نَــــوا", 
            description=f"🎵 **در حال پخش:** `ترانه-{song_num}`\n🎙️ *پخش زنده از استودیو مرکزی*", 
            color=0x9b59b6
        )
        await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'✅ Voices for the One فعال شد.')

bot.run(os.getenv('DISCORD_TOKEN'))
