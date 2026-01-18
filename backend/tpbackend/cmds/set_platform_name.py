from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Platform, User
import discord


class SetPlatformNameCommand(AdminCommand):
    def __init__(self):
        names = ["set_platform_name", "spn"]
        d = "Set platform name"
        h = f"Usage: `!{names[0]} <platform_id> <name>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) < 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        platform_id = int(splitted[0].strip())
        name = " ".join(splitted[1:]).strip()
        platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        platform.name = name
        platform.save()
        return (
            f"Platform {platform_id} (`{platform.abbreviation}`) name set to *{name}*"
        )
