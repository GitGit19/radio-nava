import discord
from discord.ext import commands
import os

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.command()
async def play(ctx):
    if not ctx.author.voice:
        return await ctx.send("ابتدا وارد کانال صوتی شوید.")

    # اتصال ساده
    vc = await ctx.author.voice.channel.connect()

    # پخش مستقیم بدون متغیرهای اضافه برای دور زدن باگ ریپلیت
    try:
        vc.play(discord.FFmpegPCMAudio("./nava1.mp3"))
        await ctx.send("📻 رادیو نوا در حال پخش است...")
    except Exception as e:
        await ctx.send(f"خطای پخش: {e}")

bot.run(os.getenv('DISCORD_TOKEN'))
