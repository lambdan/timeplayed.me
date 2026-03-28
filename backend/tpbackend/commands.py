import logging
import discord
from tpbackend.permissions import PERMISSION_COMMANDS, PERMISSION_DEVELOPER
from tpbackend.storage.storage_v2 import User, DiscordHistory
from tpbackend.globals import DEBUG

from tpbackend.command_list import REGULAR_COMMANDS, ADMIN_COMMANDS
from tpbackend.cmds.help import HelpCommand
from tpbackend.cmds.help_admin import HelpAdminCommand

logger = logging.getLogger("commands")

__CMD = 0


def user_from_message(message: discord.Message) -> User | None:
    if message.author is None:
        return None
    user, created = User.get_or_create(
        discord_id=message.author.id, name=message.author.name
    )
    if created:
        logger.info(
            "Added new user %s %s to database", message.author.id, message.author.name
        )
    return user


def dm_receive(message: discord.Message) -> str | None:
    global __CMD
    __CMD += 1

    def _info(msg: str):
        logger.info("[%s] %s", __CMD, msg)

    def _warn(msg: str):
        logger.warning("[%s] %s", __CMD, msg)

    def _err(msg: str):
        logger.error("[%s] %s", __CMD, msg)

    def _ret(reply: str | None) -> str | None:
        if reply:
            DiscordHistory.create(
                event="reply", user=str(message.author.id), message=reply
            )
            _info(f"Replying: {reply}")
            return reply
        _info("(No reply)")
        return None

    c = message.content
    _info(f"Received message from {message.author}: {c}")
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

    _info(f"User is: {user.id} ({user.name}), permissions: {user.permissions}")
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
                    _info(f"Executing command {n} with body '{body}'")
                    return _ret(c.execute(user, body))
                except Exception as e:
                    _err(f"Exception while executing command: {e}")
                    return _ret(f"Error. Maybe `!help {n}` can... help")

    return _ret("Unknown command. Use `!help` to see available commands.")
