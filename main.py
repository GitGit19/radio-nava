import discord
from discord.ext import commands
import os
import asyncio

# تنظیمات اولیه بات
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def play_next(vc):
    # پیدا کردن تمام فایل‌هایی که با nava شروع می‌شوند و پسوند mp3 دارند
    songs = sorted([f for f in os.listdir('.') if f.startswith('nava') and f.endswith('.mp3')])
    
    if not songs:
        print("هیچ فایلی با نام nava پیدا نشد!")
        return

    while True: # حلقه ابدی برای پخش مجدد از ابتدا
        for song in songs:
            print(f"در حال پخش: {song}")
            
            # پخش فایل صوتی
            source = discord.FFmpegPCMAudio(song)
            vc.play(source)
            
            # انتظار تا زمانی که آهنگ تمام شود
            while vc.is_playing():
                await asyncio.sleep(1)
            
            # یک وقفه کوتاه بین آهنگ‌ها
            await asyncio.sleep(2)

@bot.command()
async def start_radio(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = await channel.connect()
        await ctx.send("📻 رادیو نوا در حال پخش است...")
        await play_next(vc)
    else:
        await ctx.send("ابتدا باید وارد یک کانال صوتی شوید!")

bot.run(os.getenv('DISCORD_TOKEN'))
