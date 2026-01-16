import discord
from discord.ext import commands
import os
import asyncio
import re

intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True
intents.members = True 

bot = commands.Bot(command_prefix='!', intents=intents)

OWNER_ID = 350787863241031681  # آی‌دی دیسکورد من
RADIO_CHANNEL_ID = 524824235709825045  # آی‌دی کانال رادیو نَــــوا

current_index = 0
active_vc = None

def extract_number(filename):
    match = re.search(r'nava(\d+)', filename)
    return int(match.group(1)) if match else 0

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
        await interaction.response.send_message("⏪ ترانه قبلی", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        await interaction.response.send_message("📻 رادیو خاموش شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != OWNER_ID: return
        self.vc.stop()
        await interaction.response.send_message("⏩ ترانه بعدی", ephemeral=True)

async def play_logic(vc):
    global current_index, active_vc
    active_vc = vc
    
    try:
        await vc.guild.me.edit(nick="Radio Nava")
    except:
        pass

    while vc.is_connected():
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        
        if not songs: break
            
        song_file = songs[current_index % len(songs)]
        song_num = extract_number(song_file)
        
        display_text = f"در حال پخش ترانه-{song_num}"
        
        await bot.change_presence(
            activity=discord.Game(name=display_text)
        )

        vc.play(discord.FFmpegPCMAudio(song_file))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

@bot.command(name="play")
async def start_radio(ctx):
    if ctx.author.id != OWNER_ID: return
    channel = bot.get_channel(RADIO_CHANNEL_ID)
    if channel:
        if ctx.voice_client: await ctx.voice_client.disconnect()
        vc = await channel.connect()
        await ctx.send("📡 رادیو روشن شد.", delete_after=5)
        await play_logic(vc)

@bot.command(name="display")
async def display_status(ctx):
    global active_vc
    if active_vc and active_vc.is_connected():
        all_files = [f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')]
        songs = sorted(all_files, key=extract_number)
        song_num = extract_number(songs[current_index % len(songs)])
        view = RadioControl(active_vc, songs)
        embed = discord.Embed(title="📻 رادیو ۲۴ ساعته‌ی نَــــوا", 
                            description=f"🎵 **در حال پخش:** `ترانه-{song_num}`", color=0x9b59b6)
        await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f'✅ Voices for the One فعال شد.')

bot.run(os.getenv('DISCORD_TOKEN'))
