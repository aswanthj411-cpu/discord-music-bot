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

queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]


ytdl_options = {
    "format": "bestaudio/best",
    "quiet": True
}

ffmpeg_options = {
    "options": "-vn"
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data):
        super().__init__(source)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, loop=None):

        loop = loop or asyncio.get_event_loop()

        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(url, download=False)
        )

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"]

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.event
async def on_ready():
    print(f"{bot.user} is online!")


# JOIN VC
@bot.command()
async def join(ctx):

    if ctx.author.voice is None:
        await ctx.send("❌ Join a voice channel first")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"✅ Joined {channel.name}")


# LEAVE VC
@bot.command()
async def leave(ctx):

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left voice channel")


# PLAY MUSIC
@bot.command()
async def play(ctx, *, url):

    if ctx.author.voice is None:
        await ctx.send("❌ Join VC first")
        return

    if ctx.voice_client is None:
        await ctx.invoke(join)

    queue = get_queue(ctx.guild.id)

    player = await YTDLSource.from_url(url, loop=bot.loop)

    if ctx.voice_client.is_playing():
        queue.append(player)
        await ctx.send(f"📥 Added to queue: {player.title}")
    else:
        ctx.voice_client.play(
            player,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx),
                bot.loop
            )
        )
        await ctx.send(f"🎵 Now playing: {player.title}")


# PLAY NEXT SONG
async def play_next(ctx):

    queue = get_queue(ctx.guild.id)

    if len(queue) > 0:
        player = queue.pop(0)

        ctx.voice_client.play(
            player,
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx),
                bot.loop
            )
        )

        await ctx.send(f"🎵 Now playing: {player.title}")


# SKIP SONG
@bot.command()
async def skip(ctx):

    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped song")


# STOP MUSIC
@bot.command()
async def stop(ctx):

    queue = get_queue(ctx.guild.id)
    queue.clear()

    if ctx.voice_client:
        ctx.voice_client.stop()

    await ctx.send("⏹ Music stopped")


bot.run(TOKEN)
