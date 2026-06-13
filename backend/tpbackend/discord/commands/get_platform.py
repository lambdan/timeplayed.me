from tpbackend.storage import Platform_or_none, User
from .command import Command
from tpbackend.utils import platform_name
from tpbackend.utils2 import js_iso


class GetPlatformCommand(Command):
    def __init__(self):
        names = ["get_platform", "gp"]
        d = "Get platform info"
        h = "Get a platform by ID\nUsage: `!get_platform <id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        platform = Platform_or_none(int(msg))
        if not platform:
            return f"Error: platform with id {msg} not found."

        msg = ""
        msg += f"## {platform_name(platform, as_markdown_link=True)}\n"
        msg += f"- ID: {platform.id}\n"  # type: ignore
        msg += f"- Abbreviation: {platform.abbreviation}\n"
        msg += f"- Name: {'not set' if platform.name is None else platform.name}\n"
        msg += f"- Created: {js_iso(platform.get_created())}\n"
        msg += f"- Updated: {js_iso(platform.get_updated())}\n"

        if self.is_admin(user):
            msg += "\n```"
            msg += f"Color primary: {platform.color_primary}\n"
            msg += f"Color secondary: {platform.color_secondary}\n"
            msg += f"Icon: {platform.icon}\n"
            msg += "```\n"

            msg += "# History\n"
            if len(platform.get_history()) == 0:
                msg += "No history\n"
            else:
                msg += "```"
                for h in platform.get_history():
                    msg += h + "\n"
                msg += "```"

        return msg.strip()
