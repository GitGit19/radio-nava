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

# ۲. 🆔 تنظیمات اختصاصی شما
OWNER_ID = 123456789012345678  # آی‌دی دیسکورد شما
RADIO_CHANNEL_ID = 112233445566778899  # آی‌دی کانال صوتی رادیو نَــــوا

current_index = 0
active_vc = None

# تابع کمکی برای استخراج عدد واقعی از نام فایل (رفع مشکل ۱ به ۱۳)
def extract_number(filename):
    match = re.search(r'nava(\d+)', filename)
    return int(match.group(1)) if match else 0

# ۳. کلاس کنترل دکمه‌ها (کنسول مدیریتی)
class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی محدود به اپراتور است.", ephemeral=True)
            return
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ بازگشت به ترانه قبلی...", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی محدود به اپراتور است.", ephemeral=True)
            return
        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        try:
            await interaction.guild.me.edit(nick=None)
        except:
            pass
        await interaction.response.send_message("📻 پخش متوقف شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی محدود به اپراتور است.", ephemeral=True)
            return
        self.vc.stop()
        await interaction.response.send_message("⏩ ترانه بعدی...", ephemeral=True)

# ۴. منطق پخش و نمایش دقیق (Nickname & Status)
async def play_logic(vc):
    global current_index, active_vc
    active_vc = vc
    
    while vc.is_connected():
        # بازخوانی لیست فایل‌ها در هر بار چرخش برای شناسایی آهنگ‌های جدید
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        
        if not songs:
            print("❌ هیچ فایلی با نام nava پیدا نشد.")
            break
        
        song_file = songs[current_index % len(songs)]
        song_num = extract_number(song_file)
        display_text = f"در حال پخش ترانه-{song_num}"
        
        # ✨ آپدیت پروفایل
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=display_text)
        )
        
        # ✨ آپدیت نام در لیست کانال صوتی
        try:
            await vc.guild.me.edit(nick=display_text)
        except:
            pass

        # شروع پخش صدا
        vc.play(discord.FFmpegPCMAudio(song_file))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# ۵. دستورات کاربردی
@bot.command(name="play")
async def start_radio(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send(f"❌ {ctx.author.mention}، رادیو نَــــوا فقط توسط مدیر روشن می‌شود.")
        return

    channel = bot.get_channel(RADIO_CHANNEL_ID)
    if channel:
        if ctx.voice_client: await ctx.voice_client.disconnect()
        vc = await channel.connect()
        await ctx.send(f"📡 رادیو نَــــوا روشن شد.\nبرای مدیریت پخش از دستور `!display` استفاده کنید.")
        await play_logic(vc)
    else:
        await ctx.send("❌ کانال صوتی رادیو پیدا نشد! آی‌دی را در کد چک کنید.")

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
    else:
        await ctx.send("📻 رادیو خاموش است.")

# ۶. مدیریت ورود کاربران غریبه
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id or member.id == OWNER_ID: return
    if after.channel and after.channel.id == RADIO_CHANNEL_ID:
        if not discord.utils.get(bot.voice_clients, guild=member.guild):
            text_channel = member.guild.system_channel or member.guild.text_channels[0]
            if text_channel:
                await text_channel.send(f"⚠️ {member.mention} عزیز، رادیو روشن نیست!", delete_after=10)

@bot.event
async def on_ready():
    print(f'✅ Voices for the One (نَــــوا) آنلاین شد.')

bot.run(os.getenv('DISCORD_TOKEN'))
