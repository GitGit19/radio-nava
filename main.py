import discord
from discord.ext import commands
import os
import asyncio
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radio is Running")

def run_fake_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHandler)
    server.serve_forever()

# اجرای سرور در یک رشته جداگانه
threading.Thread(target=run_fake_server, daemon=True).start()

# --- تنظیمات مدیر استودیو ---
TOKEN = os.getenv('DISCORD_TOKEN')
OWNER_ID = 350787863241031681  # آی‌دی دیسکورد من
RADIO_CHANNEL_ID = 524824235709825045  # آی‌دی کانال رادیو نَــــوا

intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

current_index = 0
active_vc = None

# --- استخراج عدد برای مرتب‌سازی درست nava001, nava002 ---
def extract_number(filename):
    match = re.search(r'nava(\d+)', filename)
    return int(match.group(1)) if match else 0

# --- کلاس کنترل دکمه‌های دشبورد ---
class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ در حال بازگشت به ترانه قبلی...", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await self.vc.disconnect()
        # وضعیت خاموشی
        await bot.change_presence(
            #activity=discord.Game(name="🌙 استودیو نَــــوا در حال حاضر خاموش است")
            activity=discord.Game(name="🌙 Studio Nava | Off Air")
        )
        await interaction.response.send_message("📻 رادیو توسط مدیر متوقف شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        self.vc.stop()
        await interaction.response.send_message("⏩ در حال پخش ترانه بعدی...", ephemeral=True)

# --- منطق پخش و هماهنگی با وضعیت استودیو ---
async def play_logic(vc):
    global current_index, active_vc
    active_vc = vc
    
    # تنظیم نام نمایشی بات در لیست اعضا
    try:
        await vc.guild.me.edit(nick="Radio Nava")
    except:
        pass

    while vc.is_connected():
        # لیست کردن فایل‌های صوتی
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        
        if not songs:
            print("خطا: فایلی پیدا نشد.")
            break
            
        song_file = songs[current_index % len(songs)]
        song_num = extract_number(song_file)
        
        # پیام وضعیت در حال پخش (On Air)
        #status_text = f"رادیو نَــــوا در حال پخش است | ترانه-{song_num}"
        status_text = f"☀️ Studio Nava | On Air: Track-{song_num}"
        await bot.change_presence(activity=discord.Game(name=status_text))

        # شروع پخش صوتی
        vc.play(discord.FFmpegPCMAudio(song_file))
        
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

# --- دستورات (Commands) ---

@bot.command(name="radio")
async def start_radio(ctx):
    """فقط روشن کردن رادیو"""
    if ctx.author.id != OWNER_ID: return
    
    channel = bot.get_channel(RADIO_CHANNEL_ID)
    if channel:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        
        vc = await channel.connect()
        # ارسال پیام تایید موقت برای تمیز ماندن چت
        await ctx.send("📡 **استودیو نَــــوا آنلاین شد.**", delete_after=5)
        
        await play_logic(vc)

@bot.command(name="dashboard")
async def show_dashboard(ctx):
    """نمایش پنل مدیریت به درخواست مدیر"""
    global active_vc
    if active_vc and active_vc.is_connected():
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        song_num = extract_number(songs[current_index % len(songs)])
        
        view = RadioControl(active_vc, songs)
        embed = discord.Embed(
            title="📻 پیشخوان مدیریتی رادیو نَــــوا", 
            description=f"🎵 **وضعیت:** `در حال پخش ترانه-{song_num}`\n\n"
                        f"👤 **مدیر استودیو:** {ctx.author.mention}", 
            color=0x9b59b6
        )
        embed.set_footer(text="Voices for the One | Studio System")
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("❌ رادیو خاموش است. ابتدا `!radio` را بزنید.")

@bot.event
async def on_ready():
    print(f'✅ Voices for the One گزارش می‌دهد: بات {bot.user.name} متصل شد.')
    # وضعیت اولیه بات وقتی تازه روشن می‌شود
    await bot.change_presence(
        #activity=discord.Game(name="🌙 استودیو نَــــوا در حال حاضر خاموش است")
        activity=discord.Game(name="🌙 Studio Nava | Off Air")
    )

bot.run(TOKEN)
