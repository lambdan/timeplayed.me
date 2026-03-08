from tpbackend import api
from tpbackend.storage.storage_v2 import Platform, User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Game
from tpbackend.operations import (
    add_session,
)
from tpbackend.utils import (
    now,
    last_platform_for_game,
    search_games,
    secsToHHMMSS,
    game_url,
)


class AddActivityCommand(Command):
    def __init__(self):
        names = ["add_activity", "aa", "add"]
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

You can also *try* using the game name directly if you are lazy, but it will not work if multiple games match the name: ```
!add_activity Game Name 1:23:45
```

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) < 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game = None
        try:
            game_id = splitted[0].strip()
            game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        except Exception as e:
            # user probably did "!add_activity Game Name 1:23:45"", show search results
            # duration will be thrown into search query, but thats fine... probably
            search_results = search_games(msg, limit=10)
            if len(search_results) == 1:
                # one game found... could it be the one?
                game = search_results[0]
            elif len(search_results) > 0:
                msg = "Not sure what game you are referring to. Is it one of these?\n"
                for g in search_results:
                    msg += f"- **{g.id}** - {g.name}\n"  # type: ignore
                msg += "If so, use the game ID (the number) in the command"
                return msg
            elif len(search_results) == 0:
                return "Error: unknown game"
            else:
                raise e

        if not game:
            return "Error: Game not found"

        duration_str = splitted[-1].strip()  # last part of message
        if duration_str.count(":") != 2:
            return f"Error: invalid duration. See `!help {self.names[0]}`."

        h, m, s = duration_str.split(":")
        h, m, s = int(h), int(m), int(s)
        seconds = (h * 3600) + (m * 60) + s

        # check for overlapping?
        if self.get_overlapping(user_id=str(user.id), seconds=seconds):
            return "Error: Activity overlaps with existing activity."

        if seconds > (16 * 3600):
            return "Error: That seems a little too long..."

        return self.add(user=user, game=game, seconds=seconds)

    def get_overlapping(self, user_id: str, seconds: int) -> bool:
        after_ts = (now().timestamp() * 1000) - (seconds * 1000)
        after_ts = int(after_ts)
        activities = api.get_activities(user=user_id, after=after_ts, limit=1)
        return activities.total > 0

    def add(self, user: User, game: Game, seconds: int) -> str:
        timestamp = now()

        # get last used platform, or fallback to default
        platform = last_platform_for_game(user=user, game=game)
        if not platform:
            self.logger.debug("No last platform found, using default")
            platform = user.default_platform
        platform = Platform.get_by_id(platform.id)  # type: ignore

        result = add_session(
            user=user,
            game=game,
            seconds=seconds,
            timestamp=timestamp,
            platform=platform,
        )
        sesh = result[0]
        if sesh:
            msg = f"✅ Activity {sesh} added.\n"
            url = game_url(game.id)
            if url:
                msg += f"Game: [{game.name}]({url})\n"  # type: ignore
            else:
                msg += f"Game: {game.name}\n"  # type: ignore
            msg += f"Duration: {secsToHHMMSS(int(str(sesh.seconds)))}\n"
            msg += f"Date: {sesh.timestamp}\n"
            msg += f"Platform: {sesh.platform.name or sesh.platform.abbreviation}\n"
            return msg
        return f"ERROR: {result[1]}"
