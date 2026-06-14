from .admin_command import AdminCommand
from tpbackend.storage import Platform_or_none, User


class SetPlatformIconCommand(AdminCommand):
    def __init__(self):
        names = ["set_platform_icon", "spi"]
        d = "Set platform icon"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) < 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        platform_id = int(splitted[0].strip())
        icon = splitted[1].strip()
        platform = Platform_or_none(platform_id)
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        old_icon = platform.get_icon()
        if icon == "-" or icon == "null":
            platform.set_icon(None)
        else:
            platform.set_icon(icon)
        platform.save()
        out = f"""```
{platform.get_display_name()}:\n
icon: {old_icon} --> {platform.get_icon()}\n
        ```"""
        return out.strip()
