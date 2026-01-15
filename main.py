import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
current_index = 0

# 🆔 آی‌دی دیسکورد من
OWNER_ID = 350787863241031681  

class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # بررسی دسترسی
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ فقط صاحب رادیو می‌تواند آهنگ را تغییر دهد!", ephemeral=True)
            return
            
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ بازگشت به ترانه قبلی", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # بررسی دسترسی
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ شما اجازه خاموش کردن رادیو نَـــــــــوا را ندارید!", ephemeral=True)
            return

        await self.vc.disconnect()
        await bot.change_presence(activity=None)
        await interaction.response.send_message("📻 رادیو با دستور مدیریت خاموش شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # بررسی دسترسی
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ فقط صاحب رادیو دسترسی دارد!", ephemeral=True)
            return

        self.vc.stop()
        await interaction.response.send_message("⏩ ترانه بعدی", ephemeral=True)

async def play_logic(ctx, vc):
    global current_index
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')])
    
    if not songs:
        await ctx.send("❌ آهنگی پیدا نشد!")
        return

    view = RadioControl(vc, songs)
    while vc.is_connected():
        song = songs[current_index]
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"نـــــوا: {song}"))
        
        embed = discord.Embed(title="📻 رادیو ۲۴ ساعته‌ی نَـــــــــوا", description=f"🎵 در حال پخش: `{song}`", color=0x9b59b6)
        await ctx.send(embed=embed, view=view)
        
        vc.play(discord.FFmpegPCMAudio(song))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

@bot.command(name="play")
async def start_radio(ctx):
    # حتی دستور شروع را هم محدود کردیم
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ فقط مدیر اصلی می‌تواند رادیو را استارت بزند.")
        return

    if ctx.author.voice:
        if ctx.voice_client: await ctx.voice_client.disconnect()
        vc = await ctx.author.voice.channel.connect()
        await play_logic(ctx, vc)
    else:
        await ctx.send("❌ ابتدا وارد کانال صوتی نَـــــــــوا شوید!")

bot.run(os.getenv('DISCORD_TOKEN'))
