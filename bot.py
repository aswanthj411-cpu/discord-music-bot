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

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.gray)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client

        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("Skipped", ephemeral=True)


    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client

        if vc:
            queue.clear()
            vc.stop()
            await interaction.response.send_message("Stopped music", ephemeral=True)



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
            await message.channel.send("Join voice channel first")
            return

        channel = message.author.voice.channel

        if message.guild.voice_client is None:
            await channel.connect()

        ctx = await bot.get_context(message)

        queue.append(url)

        await message.channel.send(f"Added to queue. Position {len(queue)}")

        if not message.guild.voice_client.is_playing():
            await play_next(ctx)

    await bot.process_commands(message)


bot.run(TOKEN)
