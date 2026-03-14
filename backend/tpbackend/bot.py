import logging
import discord
from discord.ext import commands

from tpbackend.storage import storage_v2
from tpbackend.commands import dm_receive
from tpbackend.globals import DEBUG

logger = logging.getLogger("bot")

intents = discord.Intents.default()
# intents.presences = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def avatar_from_discord_user_id(id: int) -> str:
    user = bot.get_user(id)
    if user and user.display_avatar:
        return str(user.display_avatar.url)
    return f"https://cdn.discordapp.com/embed/avatars/{id % 5}.png"


@bot.event
async def on_guild_available(guild: discord.Guild):
    logger.info("Server %s available", guild)


@bot.event
async def on_ready():
    logger.info("Discord is ready")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.guild:
        # Ignore messages in channels
        return

    reply = dm_receive(message)
    if not reply:
        return

    storage_v2.DiscordHistory.create(
        event="reply", user=str(message.author.id), message=str(reply)
    )
    await message.author.send(reply, reference=message)
