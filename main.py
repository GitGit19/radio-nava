import discord
from discord.ext import commands
import os
import asyncio

# ۱. تنظیمات دسترسی‌های بات
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# ۲. 🆔 تنظیمات اختصاصی (آی‌دی‌های خود را اینجا وارد کنید)
OWNER_ID = 350787863241031681  # آی‌دی دیسکورد خودم
RADIO_CHANNEL_ID = 524824235709825045  # آی‌دی رادیو نَــــوا

current_index = 0
active_vc = None

# تابع کمکی برای ساخت نام زیبا (ترانه-X)
def get_friendly_name(filename):
    song_num = "".join(filter(str.isdigit, filename))
    return f"ترانه-{song_num}" if song_num else filename.replace('.mp3', '')

# ۳. کلاس کنترل دکمه‌ها (کنسول استودیو)
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
        await interaction.response.send_message("⏪ بازگشت به آرشیو قبلی...", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ فقط اپراتور استودیو اجازه قطع پخش را دارد.", ephemeral=True)
            return
        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        # برگرداندن نام بات به حالت عادی موقع توقف
        await interaction.guild.me.edit(nick=None)
        await interaction.response.send_message("📻 پخش برنامه از استودیو متوقف شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ دسترسی به کنسول مدیریت استودیو محدود است.", ephemeral=True)
            return
        self.vc.stop()
        await interaction.response.send_message("⏩ در حال پخش ترانه بعدی...", ephemeral=True)

# ۴. منطق پخش و مدیریت وضعیت نمایشی
async def play_logic(vc):
    global current_index, active_vc
    active_vc = vc
    # مرتب‌سازی فایل‌ها بر اساس عدد
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')],
                   key=lambda x: int("".join(filter(str.isdigit, x)) or 0))
    
    while vc.is_connected():
        song_file = songs[current_index]
        friendly_name = get_friendly_name(song_file)
        display_text = f"در حال پخش {friendly_name}"
        
        # ✨ تغییر وضعیت پروفایل (Status)
        await bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name=display_text)
        )

        # ✨ تغییر نام در کانال صوتی (Nickname)
        try:
            await vc.guild.me.edit(nick=display_text)
        except:
            pass # در صورت نبود دسترسی کافی، برنامه متوقف نشود

        vc.play(discord.FFmpegPCMAudio(song_file))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# ۵. دستورات بات
@bot.command(name="play")
async def start_radio(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send(f"❌ {ctx.author.mention}، رادیو نَــــوا فقط از استودیو روشن می‌شود.")
        return

    channel = bot.get_channel(RADIO_CHANNEL_ID)
    if channel:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        vc = await channel.connect()
        await ctx.send(f"📡 رادیو نَــــوا در کانال `{channel.name}` روشن شد.\nمدیر عزیز، برای کنترل پخش از دستور `!display` استفاده کنید.")
        await play_logic(vc)
    else:
        await ctx.send("❌ کانال رادیو پیدا نشد!")

@bot.command(name="display")
async def display_status(ctx):
    global active_vc
    if active_vc and active_vc.is_connected():
        songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')],
                       key=lambda x: int("".join(filter(str.isdigit, x)) or 0))
        friendly_name = get_friendly_name(songs[current_index])
        
        view = RadioControl(active_vc, songs)
        embed = discord.Embed(
            title="📻 رادیو ۲۴ ساعته‌ی نَــــوا", 
            description=f"🎵 **در حال پخش:** `{friendly_name}`\n🎙️ *پخش زنده از استودیو مرکزی*", 
            color=0x9b59b6
        )
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("📻 در حال حاضر رادیو خاموش است.")

# ۶. رویدادها (Events)
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id or member.id == OWNER_ID:
        return
    if after.channel and after.channel.id == RADIO_CHANNEL_ID:
        if not discord.utils.get(bot.voice_clients, guild=member.guild):
            text_channel = member.guild.system_channel or member.guild.text_channels[0]
            if text_channel:
                await text_channel.send(f"⚠️ {member.mention} عزیز، رادیو روشن نیست!\n🎙️ منتظر حضور اپراتور استودیو بمانید.", delete_after=10)

@bot.event
async def on_ready():
    print(f'✅ Voices for the One (نَــــوا) آنلاین و آماده است.')

bot.run(os.getenv('DISCORD_TOKEN'))
