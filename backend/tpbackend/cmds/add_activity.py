from tpbackend.storage.storage_v2 import Platform, User
import discord
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Game, Activity
from tpbackend.operations import (
    get_game_by_name_or_alias,
    get_game_by_name_or_alias_or_create,
    add_session,
)
from tpbackend.api import get_oldest_activity
import tpbackend.utils
import datetime


class AddActivityCommand(Command):
    def __init__(self):
        names = ["add_activity", "aa"]
        d = "Add activity manually"
        h = """
Manually add activity. Useful if you are playing on a platform that doesn't have Discord integration, and need to track manually.

Usage: `!add_activity <game_id> <duration>`

Example: add activity of 5 minutes to game 123```
!add_activity 123 0:5:0
```

Example: add activity of 1 hour, 23 minutes, 45 seconds to game 123```
!add_activity 123 1:23:45
```
Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        # remove !add_activity
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        duration_str = splitted[1].strip()

        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."

        if duration_str.count(":") != 2:
            return f"Error: invalid duration. See `!help {self.names[0]}`."

        h, m, s = duration_str.split(":")
        h, m, s = int(h), int(m), int(s)
        seconds = (h * 3600) + (m * 60) + s

        return self.add(user=user, game=game, seconds=seconds)

    def add(self, user: User, game: Game, seconds: int) -> str:
        timestamp = tpbackend.utils.now()
        result = add_session(user=user, game=game, seconds=seconds, timestamp=timestamp)
        sesh = result[0]
        if sesh:
            msg = f"Activity {sesh} added.\n"
            msg += f"Game: {game.name}\n"  # type: ignore
            msg += f"Duration: {tpbackend.utils.secsToHHMMSS(int(str(sesh.seconds)))}\n"
            msg += f"Date: {sesh.timestamp}\n"
            msg += f"Platform: {sesh.platform.abbreviation}\n"
            return msg
        return f"ERROR: {result[1]}"
