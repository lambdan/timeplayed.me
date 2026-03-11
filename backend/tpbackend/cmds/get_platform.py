from tpbackend.storage.storage_v2 import User, Platform
from tpbackend.cmds.command import Command
from tpbackend.utils import platform_name


class GetPlatformCommand(Command):
    def __init__(self):
        names = ["get_platform", "gp"]
        d = "Get platform info"
        h = "Get a platform by ID\nUsage: `!get_platform <game_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        platform = Platform.get_or_none(Platform.id == int(msg))  # type: ignore
        if not platform:
            return f"Error: platform with id {msg} not found."
        platform: Platform

        msg = ""
        msg += f"## {platform_name(platform, as_markdown_link=True)}\n"
        msg += f"- ID: {platform.id}\n"  # type: ignore
        msg += f"- Abbreviation: {platform.abbreviation}\n"
        msg += f"- Name: {"not set" if platform.name is None else platform.name}\n"

        if self.is_admin(user):
            msg += "```"
            msg += f"Color primary: {platform.color_primary}\n"
            msg += f"Color secondary: {platform.color_secondary}\n"
            msg += f"Icon: {platform.icon}\n"
            msg += "```"

        return msg.strip()
