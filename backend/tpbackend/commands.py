import datetime
import logging
import discord
from tpbackend import operations, utils
from tpbackend.storage.storage_v2 import LiveActivity, User, Game, Platform, Activity
from tpbackend.utils import sanitize

from tpbackend.command_list import REGULAR_COMMANDS, ADMIN_COMMANDS
from tpbackend.cmds.help import HelpCommand
from tpbackend.cmds.help_admin import HelpAdminCommand
from tpbackend.globals import ADMINS

logger = logging.getLogger("commands")


def user_from_message(message: discord.Message) -> User | None:
    if message.author is None:
        return None
    user, created = User.get_or_create(id=message.author.id, name=message.author.name)
    if created:
        logger.info(
            "Added new user %s %s to database", message.author.id, message.author.name
        )
    return user


def is_admin(user: User) -> bool:
    return str(user.id) in ADMINS


def dm_receive(message: discord.Message) -> str:
    content = utils.normalizeQuotes(message.content.strip())

    user = user_from_message(message)
    if user is None:
        logger.error("Could not get internal User for message: %s", message)
        return "ERROR: Try again later"

    if user.bot_commands_blocked:
        return "You are blocked from using bot commands"

    first_word = content.split(" ")[0].lower()
    cmds = [HelpCommand(), HelpAdminCommand(), *REGULAR_COMMANDS, *ADMIN_COMMANDS]
    for c in cmds:
        for n in c.names:
            if first_word == f"!{n}" and c.can_execute(user, message):
                msg = message.content.removeprefix(f"!{n}").strip()
                try:
                    logger.info(
                        "Executing `%s`, user %s, msg: '%s'...", n, user.id, msg
                    )
                    return c.execute(user, msg)
                except Exception as e:
                    logger.exception("Error executing command %s: %s", n, e)
                    return f"Error. Maybe `!help {n}` can... help"

    return "Unknown command. Use `!help` to see available commands."
