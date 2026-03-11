from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Platform, User


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
        platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        old_icon = platform.icon
        if icon == "-" or icon == "null":
            platform.icon = None
        else:
            platform.icon = icon
        platform.save()
        out = f"""```
{platform.name or platform.abbreviation}:\n
icon: {old_icon} --> {platform.icon}\n
        ```"""
        return out.strip()
