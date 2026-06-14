from tpbackend.platform.utils import display_name
from .admin_command import AdminCommand
from tpbackend.storage import Platform_or_none, User


class SetPlatformColorsCommand(AdminCommand):
    def __init__(self):
        names = ["set_platform_colors", "spc"]
        d = "Set platform colors"
        h = f"""
Usage: `!{names[0]} <platform_id> <primary hex> <secondary hex>`

Use - to skip a color, eg to set secondary color only:
`!{names[0]} <platform_id> - <secondary hex>`

Use null to remove a color:
`!{names[0]} <platform_id> null null`
"""
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) < 3:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        platform_id = int(splitted[0].strip())
        platform = Platform_or_none(platform_id)
        if not platform:
            return f"Error: Platform with id {platform_id} not found."

        primary = splitted[1].strip()
        if primary == "null":
            primary = None
        else:
            primary = primary.lstrip("#")  # remove # if user included it
        secondary = splitted[2].strip()
        if secondary == "null":
            secondary = None
        else:
            secondary = secondary.lstrip("#")  # remove # if user included it

        old_primary = platform.get_color_primary()
        old_secondary = platform.get_color_secondary()
        if primary != "-":
            platform.set_color_primary(primary)
        if secondary != "-":
            platform.set_color_secondary(secondary)
        platform.save()

        return f"""```
{display_name(platform)}:\n
primary: {old_primary} --> {platform.get_color_primary()}\n
secondary: {old_secondary} --> {platform.get_color_secondary()}
        ```"""
