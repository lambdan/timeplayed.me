from tpbackend.storage.storage_v2 import Platform, User, Platform
import discord
from tpbackend.cmds.command import Command


class SetDefaultPlatformCommand(Command):
    def __init__(self):
        names = ["set_default_platform", "set_dp", "sdp", "platform"]
        d = "Set default platform"
        h = """
Set your default platform. This will be used when adding activities manually.

Use without argument to see your current default platform.

Example: check your current default platform```
!platform
```

Example: set your default platform to platform 2```
!platform 2
```

Use `!platforms` to see available platforms. Only admins can add new platforms.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        # remove command prefix
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        if msg == "":
            return self.get_current(user)

        platform_id = int(msg)
        platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        return self.update(user, platform)

    def get_current(self, user: User) -> str:
        platform = user.default_platform
        return f"Your current default platform is: {platform.abbreviation} (id: {platform.id})"  # type: ignore

    def update(self, user: User, new_platform: Platform) -> str:
        user.default_platform = new_platform  # type: ignore
        user.save()
        return f"Your default platform is now **{new_platform.abbreviation}** (id: {new_platform.id})"  # type: ignore
