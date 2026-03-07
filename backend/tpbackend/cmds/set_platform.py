from tpbackend.storage.storage_v2 import Platform, User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Activity
from tpbackend.utils import search_platforms


class SetPlatformCommand(Command):
    def __init__(self):
        names = ["set_platform", "sp"]
        d = "Set platform of activity"
        h = """
Change platform of an activity or activities.

Usage: `!set_platform <activity_id> <platform_id>`
Example: set activity 123 to platform 2```
!set_platform 123 2 
```
Can also change multiple activities at once.

Example: set activities 123, 124 and 125 to platform 3: ```
!set_platform 123,124,125 3 
```

If you are lazy you can also *try* to use the name/abbreviation directly:
```
!set_platform 123 snes
```
But it will not work if there are multiple matches.

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) < 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        activities = splitted[0].split(",")
        platform = None
        try:
            platform_id = int(splitted[1].strip())
            platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        except Exception:
            # hmm maybe user did !set_platform 123 snes, try searching for it!
            search_results = search_platforms(" ".join(splitted[1:]))
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
            return "Error: platform not found"
        return self.set_platform(user, activities, platform)

    def set_platform(
        self, user: User, activity_ids: list[str], platform: Platform
    ) -> str:
        msg = ""
        for activity_id in activity_ids:
            act = Activity.get_or_none(Activity.id == int(activity_id))  # type: ignore
            if not act:
                msg += f"- {activity_id}: ❌ not found\n"
                continue
            if act.user.id != user.id:
                msg += f"- {activity_id}: ❌ not yours!\n"
                continue
            old_platform = act.platform.abbreviation
            act.platform = platform
            act.save()
            msg += f"- {activity_id}: {old_platform} -> {act.platform.abbreviation}\n"
        return msg
