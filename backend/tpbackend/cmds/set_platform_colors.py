from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Platform, User


class SetPlatformColorsCommand(AdminCommand):
    def __init__(self):
        names = ["set_platform_colors", "spc"]
        d = "Set platform colors"
        h = f"""
Usage: `!{names[0]} <platform_id> <primary hex> <secondary hex>`

Use - to skip a color, eg to set secondary color only:
`!{names[0]} <platform_id> - <secondary hex>`
"""
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) < 3:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        platform_id = int(splitted[0].strip())
        primary = splitted[1].strip()
        secondary = splitted[2].strip()
        platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        old_primary = platform.color_primary
        old_secondary = platform.color_secondary
        if primary != "-":
            platform.color_primary = primary
        if secondary != "-":
            platform.color_secondary = secondary
        platform.save()
        out = f"""```
{platform.name or platform.abbreviation}:\n
primary: {old_primary} --> {platform.color_primary}\n
secondary: {old_secondary} --> {platform.color_secondary}
        ```"""
        return out.strip()
