from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.operations import (
    get_game_by_name_or_alias,
    get_game_by_name_or_alias_or_create,
)
from tpbackend.api import get_oldest_activity
import datetime


class AddGameCommand(Command):
    def __init__(self):
        names = ["add_game"]
        d = "Add game to the database"
        h = """
Add a new game to the database. Useful if you need to track a game manually.

NOTE: Command is only allowed for users that have previous activity, 
and the oldest activity is at least 48 hours old.
In other words: you must've been a member for 2 days.

Usage: `!add_game <game_name>`
Example: ```
!add_game The Legend of Zelda: Breath of the Wild
```
Returns: Confirmation message with the game ID and name.
        """
        super().__init__(names=names, description=d, help=h)

    def allowed(self, user: User, msg: str) -> bool:
        if self.is_admin(user):
            return True
        if not super().can_execute(user, msg):
            return False
        oldest_activity = get_oldest_activity(userid=str(user.id))
        if oldest_activity is None:
            return False  # no activity
        ts = oldest_activity.timestamp  # ms
        now = datetime.datetime.utcnow().timestamp()  # secs
        now_ms = int(now * 1000)
        diff_ms = now_ms - ts
        if diff_ms < (48 * 60 * 60 * 1000):
            return False  # less than 48 hours
        return True

    def execute(self, user: User, msg: str) -> str:
        if not self.allowed(user, msg):
            return "You are not allowed to use this command... yet... See `!help add_game` for more info."
        name = msg
        if name == "":
            return f"No game name provided? Try `!help {self.names[0]}` for help"
        return self.add(name)

    def add(self, s: str) -> str:
        game = get_game_by_name_or_alias(s)
        if game:
            return f"Error: Game seems to already exist: '{game.name}' (id: {game.id})"  # type: ignore
        game = get_game_by_name_or_alias_or_create(s)
        return f"✅ Game added: *{game.name}* (id: {game.id})"  # type: ignore
