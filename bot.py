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

queue = []
volume = 0.5


class MusicButtons(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔊 Vol +", style=discord.ButtonStyle.green)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc and vc.source:
            vc.source.volume = min(vc.source.volume + 0.1, 2)
            await interaction.response.send_message("Volume Increased", ephemeral=True)

    @discord.ui.button(label="🔉 Vol -", style=discord.ButtonStyle.blurple)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc and vc.source:
            vc.source.volume = max(vc.source.volume - 0.1, 0)
            await interaction.response.send_message("Volume Decreased", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.gray)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await interaction.response.send_message("Skipped")

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            queue.clear()
            vc.stop()
            await interaction.response.send_message("Stopped and cleared queue")


async def play_next(ctx):

    if len(queue) == 0:
        return

    url = queue.pop(0)

    ydl_opts = {"format": "bestaudio"}
    loop = asyncio.get_event_loop()

    data = await loop.run_in_executor(
        None,
        lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=False)
    )

    stream = data["url"]
    title = data["title"]

    vc = ctx.guild.voice_client

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream))
    source.volume = volume

    def after_playing(error):
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except:
            pass

    vc.play(source, after=after_playing)

    await ctx.send(f"🎵 Now Playing: {title}", view=MusicButtons())


@bot.event
async def on_ready():
    print("Bot Online")


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if bot.user in message.mentions and "play" in message.content:

        parts = message.content.split()

        if len(parts) < 3:
            await message.channel.send("Send a YouTube link")
            return

        url = parts[-1]

        if message.author.voice is None:
            await message.channel.send("Join a voice channel first")
            return

        channel = message.author.voice.channel

        if message.guild.voice_client is None:
            await channel.connect()

        ctx = await bot.get_context(message)

        queue.append(url)

        await message.channel.send(f"Added to queue. Position: {len(queue)}")

        if not message.guild.voice_client.is_playing():
            await play_next(ctx)

    await bot.process_commands(message)


bot.run(TOKEN)    def __init__(self, source, *, data):
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
