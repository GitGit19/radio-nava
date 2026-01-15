import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# متغیری برای ذخیره وضعیت پخش در هر سرور
current_index = 0

class RadioControl(View):
    def __init__(self, vc, songs):
        super().__init__(timeout=None)
        self.vc = vc
        self.songs = songs

    @discord.ui.button(label="قبلی", style=discord.ButtonStyle.secondary, emoji="prev:123456") # یا ⏪
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global current_index
        if self.vc.is_connected():
            current_index = (current_index - 2) % len(self.songs) # رفتن به دو تا عقب چون یکی جلو می‌رود
            self.vc.stop()
            await interaction.response.send_message("⏪ بازگشت به ترانه‌ی قبلی", ephemeral=True)

    @discord.ui.button(label="توقف", style=discord.ButtonStyle.danger, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_connected():
            await self.vc.disconnect()
            await interaction.response.send_message("📻 رادیو خاموش شد.", ephemeral=True)

    @discord.ui.button(label="بعدی", style=discord.ButtonStyle.secondary, emoji="next:123456") # یا ⏩
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.is_playing():
            self.vc.stop()
            await interaction.response.send_message("⏩ رفتن به ترانه‌ی بعدی", ephemeral=True)

async def play_radio(ctx, vc):
    global current_index
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')])
    
    if not songs:
        await ctx.send("❌ فایلی پیدا نشد!")
        return

    view = RadioControl(vc, songs)
    current_index = 0

    while vc.is_connected():
        song = songs[current_index]
        
        embed = discord.Embed(
            title="📻 رادیو ۲۴ ساعته‌ی نـــــوا",
            description=f"🎵 **در حال پخش:** `{song}`\n🔢 ترک شماره `{current_index + 1}` از `{len(songs)}`",
            color=discord.Color.purple()
        )
        
        await ctx.send(embed=embed, view=view)
        
        vc.play(discord.FFmpegPCMAudio(song))
        
        while vc.is_playing():
            await asyncio.sleep(1)
        
        # رفتن به آهنگ بعدی (با قابلیت تکرار لیست)
        current_index = (current_index + 1) % len(songs)
        
        if not vc.is_connected():
            break
        await asyncio.sleep(1)

@bot.command()
async def start_radio(ctx):
    if ctx.author.voice:
        vc = await ctx.author.voice.channel.connect()
        await play_radio(ctx, vc)
    else:
        await ctx.send("❌ ابتدا وارد یک کانال صوتی شوید!")

bot.run(os.getenv('DISCORD_TOKEN'))
