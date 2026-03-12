import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data):
        super().__init__(source)
        self.data = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url, loop=None):

        ydl_opts = {"format": "bestaudio"}

        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None,
            lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False),
        )

        filename = data["url"]

        return cls(discord.FFmpegPCMAudio(filename), data=data)


@bot.event
async def on_ready():
    print("Bot Online")


# FIXED JOIN COMMAND
@bot.command()
async def join(ctx):

    if ctx.author.voice is None:
        await ctx.send("❌ You must join a voice channel first.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"✅ Joined **{channel.name}**")


@bot.command()
async def play(ctx, *, url):

    if not ctx.author.voice:
        await ctx.send("❌ Join VC first")
        return

    if ctx.voice_client is None:
        await ctx.invoke(join)

    player = await YTDLSource.from_url(url, loop=bot.loop)

    ctx.voice_client.play(player)

    await ctx.send(f"🎵 Now playing {player.title}")


bot.run(TOKEN)

@bot.event
async def on_ready():
    print("Bot Online")


@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()


@bot.command()
async def play(ctx, *, url):

    if not ctx.author.voice:
        await ctx.send("Join VC first")
        return

    if ctx.voice_client is None:
        await ctx.invoke(join)

    player = await YTDLSource.from_url(url, loop=bot.loop)

    ctx.voice_client.play(player)

    await ctx.send(f"Now playing {player.title}")


bot.run(TOKEN)
