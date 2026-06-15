from .admin_command import AdminCommand
from tpbackend.storage import Platform, Platform_or_none, User


class AddPlatformCommand(AdminCommand):
    def __init__(self):
        names = ["add_platform", "ap"]
        d = "Add new platform"
        h = f"Usage: `!{names[0]} <abbreviation>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        abbr = msg.lower().strip()
        if len(abbr) == 0:
            return "Error: abbreviation cannot be empty"
        platform = Platform.get_or_none(Platform.abbreviation == abbr)  # type: ignore
        if platform:
            return f"Error: Platform with abbreviation {abbr} already exists."
        platform, created = Platform.get_or_create(abbreviation=abbr)  # type: ignore
        if not created:
            return "Error: platform was not created"

        p = Platform_or_none(platform.id)
        if p:
            p.add_history(f"Platform added by command by {user.name}")
            p.save()

        return f"✅ Platform {abbr} added, id {platform.id}"
