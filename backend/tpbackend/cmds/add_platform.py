from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Platform, User
import discord
from tpbackend.storage.storage_v2 import Game


class AddPlatformCommand(AdminCommand):
    def __init__(self):
        names = ["add_platform"]
        d = "Add new platform"
        h = f"Usage: `!{names[0]} <abbreviation>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 1:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        abbr = splitted[0].strip().lower()
        platform = Platform.get_or_none(Platform.abbreviation == abbr)  # type: ignore
        if platform:
            return f"Error: Platform with abbreviation {abbr} already exists."
        platform, created = Platform.get_or_create(abbreviation=abbr)  # type: ignore
        if not created:
            return "Error: platform was not created"
        return f"Platform {abbr} added, id {platform.id}"
