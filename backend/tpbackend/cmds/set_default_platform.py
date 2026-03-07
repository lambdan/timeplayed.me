from tpbackend.storage.storage_v2 import Platform, User
from tpbackend.cmds.command import Command
from tpbackend.utils import search_platforms


class SetDefaultPlatformCommand(Command):
    def __init__(self):
        names = [
            "set_default_platform",
            "set_dp",
            "sdp",
            "platform",
            "dp",
            "default_platform",
        ]
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

If you are lazy, you can also *try* to use the name/abbreviation directly:
```!platform snes
```
But it will not work if there are multiple matches.

Use `!platforms` to see available platforms. Only admins can add new platforms.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        if msg == "":
            return self.get_current(user)

        platform = None
        try:
            platform_id = int(msg)
            platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        except Exception:
            # hmm maybe user did !platform snes, try searching for it!
            search_results = search_platforms(msg)
            if len(search_results) == 1:
                platform = search_results[0]
            elif len(search_results) > 1:
                msg = (
                    "Not sure what platform you are referring to. Is it one of these?\n"
                )
                for p in search_results:
                    msg += f"- **{p.id}** - {p.name or p.abbreviation}\n"  # type: ignore
                msg += "If so, use the platform ID (the number) in the command"
                return msg
        if not platform:
            return "Error: Platform not found"
        return self.update(user, platform)

    def get_current(self, user: User) -> str:
        platform = user.default_platform
        return f"Your default platform is: **{platform.abbreviation}** (id: {platform.id}).\nSee `!platforms` for available platforms, and use `!set_default_platform n` to change your default."  # type: ignore

    def update(self, user: User, new_platform: Platform) -> str:
        user.default_platform = new_platform  # type: ignore
        user.save()
        return f"Your default platform is now **{new_platform.abbreviation}** (id: {new_platform.id})"  # type: ignore
