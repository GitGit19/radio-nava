import discord
from discord.ext import commands
import os
import asyncio

# تنظیمات دقیق دسترسی‌ها
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# متغیر سراسری برای کنترل آهنگ‌ها
current_index = 0

class RadioControl(discord.ui.View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="⏪")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_index
        current_index = (current_index - 2) % len(self.songs)
        self.vc.stop()
        await interaction.response.send_message("⏪ ترانه قبلی", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vc.disconnect()
        await interaction.response.send_message("📻 رادیو خاموش شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="⏩")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.vc.stop()
        await interaction.response.send_message("⏩ ترانه بعدی", ephemeral=True)

async def play_logic(ctx, vc):
    global current_index
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')])
    
    if not songs:
        await ctx.send("❌ آهنگی با پیشوند nava پیدا نشد!")
        return

    view = RadioControl(vc, songs)
    while vc.is_connected():
        song = songs[current_index]
        embed = discord.Embed(title="📻 رادیو ۲۴ ساعته‌ی نـــــوا", 
                              description=f"🎵 در حال پخش: `{song}`", color=0x9b59b6)
        await ctx.send(embed=embed, view=view)
        
        vc.play(discord.FFmpegPCMAudio(song))
        while vc.is_playing():
            await asyncio.sleep(1)
        
        current_index = (current_index + 1) % len(songs)
        await asyncio.sleep(1)

@bot.command(name="start_radio", aliases=["play", "radio"])
async def start_radio(ctx):
    print(f"Command received from: {ctx.author}") # این در لاگ کویب چاپ می‌شود
    if ctx.author.voice:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        vc = await ctx.author.voice.channel.connect()
        await play_logic(ctx, vc)
    else:
        await ctx.send("❌ ابتدا وارد یک کانال صوتی شوید!")

@bot.event
async def on_ready():
    print(f'✅ Voices for the One is online as {bot.user}')

bot.run(os.getenv('DISCORD_TOKEN'))
