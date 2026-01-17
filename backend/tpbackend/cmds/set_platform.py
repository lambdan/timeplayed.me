from tpbackend.storage.storage_v2 import Platform, User
import discord
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Game, Activity
from tpbackend.operations import (
    get_game_by_name_or_alias,
    get_game_by_name_or_alias_or_create,
)
from tpbackend.api import get_oldest_activity
import datetime


class SetPlatformCommand(Command):
    def __init__(self):
        names = ["set_platform", "sp"]
        d = "Set platform of activity"
        h = """
Change platform of an activity or activities.

Usage: `!set_platform <activity_id> <platform_id>`
Example: set activity 123 to platform 2```
!set_game 123 2 
```
Can also change multiple activities at once.

Example: set activities 123, 124 and 125 to platform 3: ```
!set_game 123,124,125 3 
```

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        # remove !set_platform
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        activities = splitted[0].split(",")
        platform_id = splitted[1].strip()
        return self.set_platform(user, activities, platform_id)

    def set_platform(
        self, user: User, activity_ids: list[str], platform_id: str
    ) -> str:
        platform = Platform.get_or_none(Platform.id == int(platform_id))  # type: ignore
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        msg = ""
        for activity_id in activity_ids:
            act = Activity.get_or_none(Activity.id == int(activity_id))  # type: ignore
            if not act:
                msg += f"- {activity_id}: ❌ not found\n"
                continue
            if act.user.id != user.id:
                msg += f"- {activity_id}: ❌ not yours!\n"
                continue
            act.platform = platform
            act.save()
            msg += f"- {activity_id}: updated\n"
        return msg
