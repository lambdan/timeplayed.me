import logging
import discord
from tpbackend.permissions import Permission
from tpbackend.storage import User, DiscordHistory
from tpbackend.globals import DEBUG

from .command_list import COMMANDS
from .commands.help import HelpCommand

from discord.ext import commands

logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True
# for tracking what members play (presence.py). Privileged, must be enabled for the bot in the Discord developer portal
intents.presences = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# dev and prod run with the same bot token, so each only answers its own prefix:
# ! in prod, . while developing (and then only for users with the developer permission)
PREFIX = "." if DEBUG else "!"

__CMD = 0


def get_discord_user(id: int | str) -> discord.User | None:
    return bot.get_user(int(id))


def default_avatar_url(id: int | str) -> str:
    return f"https://cdn.discordapp.com/embed/avatars/{int(id) % 5}.png"  # same as default avatar url...


def avatar_from_discord_user_id(id: int | str) -> str:
    user = get_discord_user(id)
    if user and user.display_avatar:
        return str(user.display_avatar.url)
    if user and user.default_avatar:
        return str(user.default_avatar.url)
    return default_avatar_url(id)


def user_from_message(message: discord.Message) -> User:
    user, created = User.from_discord(message.author.id, message.author.name)
    if created:
        logger.info(
            "Added new user %s %s to database", message.author.id, message.author.name
        )
        user.add_history("Created from DM message")
        user.save()
    user.sync_name(message.author.name)
    user.sync_display_name(message.author.display_name)
    return user


def dm_receive(message: discord.Message) -> str | None:
    global __CMD
    __CMD += 1

    def _info(msg: str):
        logger.info("[CMD#%s] %s", __CMD, msg)

    def _warn(msg: str):
        logger.warning("[CMD#%s] %s", __CMD, msg)

    def _err(msg: str):
        logger.error("[CMD#%s] %s", __CMD, msg)

    def _ret(reply: str | None, sensitive=False) -> str | None:
        if reply:
            # sensitive replies (like tokens) are only sent to the user, never logged or stored
            logged = "<redacted>" if sensitive else reply
            DiscordHistory.create(
                event="reply", user=str(message.author.id), message=logged
            )
            _info(f"<REPLY> {logged}")
            return reply
        _info("(No reply)")
        return None

    c = message.content
    _info(f"<{message.author}> {c}")

    if not c.startswith(PREFIX):
        _warn(f"Ignoring because it doesn't start with {PREFIX}")
        return _ret(None)

    user = user_from_message(message)

    _info(f"User is: {user.id} {user.name}, permissions: {user.permissions}")
    if DEBUG and not user.has_permission(Permission.DEVELOPER):
        _warn("Ignoring because user doesn't have developer permission")
        return _ret(None)

    DiscordHistory.create(
        event="received_message",
        user=str(message.author.id),
        message=str(message.content),
    )

    if not user.has_permission(Permission.COMMANDS):
        return _ret("You don't have permission to use commands.")

    content = message.content.strip()  # utils.normalizeQuotes(message.content.strip())
    in_cmd = content.split(" ")[0].lower()[1:]  # first word (command) + remove ! or .
    body = " ".join(content.split(" ")[1:])  # remove command
    cmds = [HelpCommand(), *COMMANDS]
    for c in cmds:
        for n in c.names:
            if in_cmd == n and c.can_execute(user, body):
                try:
                    _info(f"Executing command `{n}` with body `{body}`")
                    return _ret(c.execute(user, body), sensitive=c.sensitive_reply)
                except Exception as e:
                    _err(f"Exception while executing command: {e}")
                    return _ret(f"Error. Maybe `!help {n}` can... help")

    return _ret("Unknown command. Use `!help` to see available commands.")


def channel_command(content: str) -> str | None:
    """The command in a channel message, like "token" for "!token", if it's one of ours"""
    if not content.startswith(PREFIX):
        return None
    name = content.strip().split(" ")[0][len(PREFIX) :].lower()
    for command in [HelpCommand(), *COMMANDS]:
        if name in command.names:
            return name
    return None


async def channel_receive(message: discord.Message):
    # The bot never posts in channels, they stay silent. Someone posting a command there
    # (newcomers do) gets a 👀 on it and a DM pointing them to the DMs, nothing else.
    if message.author.bot:
        return
    name = channel_command(message.content)
    if not name:
        return
    if DEBUG:
        user = User.get_or_none(User.discord_id == str(message.author.id))
        if not user or not user.has_permission(Permission.DEVELOPER):
            return
    logger.info(
        "%s posted %s%s in #%s, pointing them to DMs",
        message.author,
        PREFIX,
        name,
        message.channel,
    )
    await point_to_dms(message)


async def point_to_dms(message: discord.Message):
    # either can fail (no permission to react, DMs from server members turned off),
    # then the other one still happens and nothing ends up in the channel
    try:
        await message.add_reaction("👀")
    except discord.HTTPException as e:
        logger.warning("Could not react to %s's message: %s", message.author, e)
    try:
        await message.author.send(
            f"Commands only work in DMs with me. Send `{PREFIX}help` here to see what's available."
        )
    except discord.HTTPException as e:
        logger.warning("Could not DM %s: %s", message.author, e)


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
        await channel_receive(message)
        return

    reply = dm_receive(message)
    if not reply:
        return

    await message.author.send(reply, reference=message)
