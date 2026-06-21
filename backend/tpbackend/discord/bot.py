import logging
from typing import cast
import discord
from tpbackend.permissions import PERMISSION_COMMANDS, PERMISSION_DEVELOPER
from tpbackend.storage import User, DiscordHistory
from tpbackend.globals import DEBUG

from .command_list import REGULAR_COMMANDS, ADMIN_COMMANDS
from .commands.help import HelpCommand
from .commands.help_admin import HelpAdminCommand

import discord
from discord.ext import commands


logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

__CMD = 0


def get_discord_user(id: int | str) -> discord.User | None:
    return bot.get_user(int(id))


def avatar_from_discord_user_id(id: int | str) -> str:
    user = get_discord_user(id)
    if user and user.display_avatar:
        return str(user.display_avatar.url)
    if user and user.default_avatar:
        return str(user.default_avatar.url)
    return f"https://cdn.discordapp.com/embed/avatars/{id % 5}.png"  # same as default avatar url...


def user_from_message(message: discord.Message) -> User | None:
    if message.author is None:
        return None
    user, created = User.get_or_create(
        discord_id=message.author.id,
        name=message.author.name,
    )
    if created:
        logger.info(
            "Added new user %s %s to database", message.author.id, message.author.name
        )
        user.add_history("Created from DM message")
        user.save()
    user = cast(User, user)
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

    def _ret(reply: str | None) -> str | None:
        if reply:
            DiscordHistory.create(
                event="reply", user=str(message.author.id), message=reply
            )
            _info(f"<REPLY> {reply}")
            return reply
        _info("(No reply)")
        return None

    c = message.content
    _info(f"<{message.author}> {c}")
    # ! in prod
    # . while developing

    if not c.startswith("!") and not c.startswith("."):
        # ignore messages without ! or .
        _warn("Ignoring because it doesn't have prefix")
        return _ret(None)

    user = user_from_message(message)
    if not user:
        _err(f"Could not find or create user for message author {message.author}")
        return _ret(None)

    _info(f"User is: {user.id} {user.name}, permissions: {user.permissions}")
    if DEBUG:
        if not user.has_permission(PERMISSION_DEVELOPER):
            _warn("Ignoring because user doesn't have developer permission")
            return _ret(None)
        if c.startswith("!"):
            _warn("Ignoring prod message")
            return _ret(None)
    if not DEBUG and c.startswith("."):
        _warn("Ignoring dev message in prod")
        return _ret(None)

    DiscordHistory.create(
        event="received_message",
        user=str(message.author.id),
        message=str(message.content),
    )

    if not user.has_permission(PERMISSION_COMMANDS):
        return _ret("You don't have permission to use commands.")

    content = message.content.strip()  # utils.normalizeQuotes(message.content.strip())
    in_cmd = content.split(" ")[0].lower()[1:]  # first word (command) + remove ! or .
    body = " ".join(content.split(" ")[1:])  # remove command
    cmds = [HelpCommand(), HelpAdminCommand(), *REGULAR_COMMANDS, *ADMIN_COMMANDS]
    for c in cmds:
        for n in c.names:
            if in_cmd == n and c.can_execute(user, body):
                try:
                    _info(f"Executing command `{n}` with body `{body}`")
                    return _ret(c.execute(user, body))
                except Exception as e:
                    _err(f"Exception while executing command: {e}")
                    return _ret(f"Error. Maybe `!help {n}` can... help")

    return _ret("Unknown command. Use `!help` to see available commands.")


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

    await message.author.send(reply, reference=message)
