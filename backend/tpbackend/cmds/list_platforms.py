from tpbackend.storage.storage_v2 import User, Platform
import discord
from tpbackend.cmds.command import Command


class ListPlatformsCommand(Command):
    def __init__(self):
        super().__init__(
            ["platforms", "list_platforms", "plist", "listp", "pl"],
            "List available platforms",
        )

    def execute(self, user: User, message: discord.Message) -> str:
        platforms = Platform.select().order_by(Platform.abbreviation)
        msg = "```"
        for p in platforms:
            padded_id = str(p.id).rjust(3, " ")
            padded_abbr = p.abbreviation.ljust(12, " ")
            msg += f"{padded_id}: {padded_abbr}\t{p.name if p.name else ""}\n"
        msg += "```"
        return msg
