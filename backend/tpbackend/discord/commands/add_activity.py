from typing import cast
from tpbackend.activity.query import ActivityQuery
from tpbackend.game.query import GameQuery
from tpbackend.game.select import GameSelect
from tpbackend.discord.commands.manual_activity_command import ManualActivityCommand
from tpbackend.storage import Platform, User
from tpbackend.storage import Game
from tpbackend.operations import (
    add_session,
)
from tpbackend.utils import (
    activity_name,
    game_name,
    last_platform_for_game,
)

from tpbackend.utils2 import secsToHHMMSS, now


class AddActivityCommand(ManualActivityCommand):
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
            game = GameSelect.by_id(game_id)
        except Exception as e:
            # user probably did "!add_activity Game Name 1:23:45"", show search results
            search_query = " ".join(splitted[:-1]).strip()
            search_results = (
                GameQuery.search(GameQuery.base(), search=search_query)
                .limit(5)
                .execute()
            )
            if len(search_results) == 1:
                # one game found... could it be the one?
                game = search_results[0]
                self.logger.info(f"One result! {game}")
            elif len(search_results) > 0:
                msg = "Not sure what game you are referring to. Is it one of these?\n"
                for g in search_results:
                    msg += f"- **{g.id}** - {game_name(g, as_markdown_link=True)}\n"  # type: ignore
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
        if self.get_overlapping(user_id=user.id, seconds=seconds):  # type: ignore
            return "Error: Activity overlaps with existing activity."

        if seconds > (16 * 3600):
            return "Error: That seems a little too long..."

        return self.add(user=user, game=game, seconds=seconds)

    def get_overlapping(self, user_id: int, seconds: int) -> bool:
        after_ts = (now().timestamp() * 1000) - (seconds * 1000)
        after_ts = int(after_ts)
        query = ActivityQuery.base()
        query = ActivityQuery.user(query, user_id)
        query = ActivityQuery.after(query, after_ts)
        return ActivityQuery.count(query) > 0

    def add(self, user: User, game: Game, seconds: int) -> str:
        timestamp = now()

        # get last used platform, or fallback to default
        platform = last_platform_for_game(user=user, game=game)
        if not platform:
            self.logger.debug("No last platform found, using default")
            platform = user.get_default_platform()
        platform = Platform.get_by_id(platform.id)
        platform = cast(Platform, platform)

        result = add_session(
            user=user,
            game=game,
            seconds=seconds,
            timestamp=timestamp,
            platform=platform,
        )
        sesh = result[0]
        if sesh:
            formatted_dt = sesh.get_datetime().strftime("%Y-%m-%d %H:%M:%S UTC")
            msg = f"{activity_name(sesh, as_markdown_link=True)} added ✅\n"
            msg += f"- Game: {game_name(game=sesh.get_game(), as_markdown_link=True)}\n"  # type: ignore
            msg += f"- Duration: {secsToHHMMSS(sesh.get_seconds())}\n"
            msg += f"- Date: {formatted_dt}\n"
            msg += f"- Platform: {sesh.get_platform().get_display_name()}\n"

            sesh.add_history("Activity source: manual add command")
            sesh.save()

            return msg.strip()
        return f"ERROR: {result[1]}"
