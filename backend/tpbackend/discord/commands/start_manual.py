from tpbackend.game.query import GameQuery
from tpbackend.game.select import GameSelect
from tpbackend.game.utils import md_game_link
from .manual_activity_command import ManualActivityCommand
from tpbackend.storage import (
    LiveActivity_or_none,
    User,
    LiveActivity,
    Game,
)
from tpbackend.platform.utils import last_platform_for_game
from tpbackend.utils2 import now


class StartManualCommand(ManualActivityCommand):
    def __init__(self):
        names = ["start"]
        d = "Start manual activity"
        h = """
Start manual activity for a game. Useful if you are playing on a platform that doesn't have Discord integration, and need to track manually.
Usage: `!start <game_id>`

Example: start playing game 5```
!start 5
```

You can also *try* using the game name directly if you are lazy, but it will not work if multiple games match the name: ```
!start Game Name
```

Use the stop command when you are done playing to save the activity.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        try:
            splitted = msg.split(" ")
            game_id = splitted[0].strip()
            game = GameSelect.by_id(int(game_id))
            if not game:
                return f"Error: Game with id {game_id} not found."
            return self.start(user=user, game=game)
        except Exception as e:
            # user probably did "!start Game Name""
            search_results = (
                GameQuery.search(GameQuery.base(), search=msg).limit(10).execute()
            )
            if len(search_results) == 1:
                # one game found... could it be the one?
                return self.start(user=user, game=search_results[0])
            elif len(search_results) > 0:
                msg = "Not sure what game you are referring to. Is it one of these?\n"
                for g in search_results:
                    msg += f"- {md_game_link(g)} ({g.id})\n"
                msg += "If so, use the game ID (the number) in the command"
                return msg
            elif len(search_results) == 0:
                return "Error: unknown game"
            else:
                raise e

    def start(self, user: User, game: Game) -> str:

        runningSession = LiveActivity_or_none(user=user)
        if runningSession:
            return "You already have a manual activity running, stop it first."

        # get last used platform, or fallback to default
        platform = last_platform_for_game(user=user, game=game)
        if not platform:
            self.logger.debug("No last platform found, using default platform")
            platform = user.get_default_platform()

        started = now()
        LiveActivity.create(user=user, game=game, platform=platform, started=started)
        return (
            f"⏱️ Started playing *{md_game_link(game)}*. Send `!stop` when you are done."
        )
