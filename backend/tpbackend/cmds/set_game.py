from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Game, Activity
from tpbackend.operations import (
    get_game_by_name_or_alias,
    get_game_by_name_or_alias_or_create,
)
from tpbackend.api import get_oldest_activity
import datetime


class SetGameCommand(Command):
    def __init__(self):
        names = ["set_game", "sg"]
        d = "Change game of activity/activities"
        h = """
Change game of an activity or activities. Useful if you've played a game in an emulator, and want to change it to the actual game.

Usage: `!set_game <activity_id> <game_id>`
Example: set activity 123 to game 456```
!set_game 123 456
```
Can also change multiple activities at once.

Example: set activities 123, 124 and 125 to game 456: ```
!set_game 123,124,125 456
```

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        # remove !set_game
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        activities = splitted[0].split(",")
        game_id = splitted[1].strip()
        return self.set_game(user, activities, game_id)

    def set_game(self, user: User, activity_ids: list[str], game_id: str) -> str:
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        msg = ""
        for activity_id in activity_ids:
            act = Activity.get_or_none(Activity.id == int(activity_id))  # type: ignore
            if not act:
                msg += f"- {activity_id}: ❌ not found\n"
                continue
            if act.user.id != user.id:
                msg += f"- {activity_id}: ❌ not yours!\n"
                continue
            act.game = game
            act.save()
            msg += f"- {activity_id}: updated\n"
        return msg
