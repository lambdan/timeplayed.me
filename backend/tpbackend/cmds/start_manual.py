from tpbackend.storage.storage_v2 import User, LiveActivity, Game
from tpbackend.cmds.command import Command
import tpbackend.utils
from tpbackend.utils import last_platform_for_game


class StartManualCommand(Command):
    def __init__(self):
        names = ["start"]
        d = "Start manual activity"
        h = """
Start manual activity for a game. Useful if you are playing on a platform that doesn't have Discord integration, and need to track manually.
Usage: `!start <game_id>`

Example: start playing game 5```
!start 5
```

Use the stop command when you are done playing to save the activity.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 1:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        return self.start(user=user, game=game)

    def start(self, user: User, game: Game) -> str:

        runningSession = LiveActivity.get_or_none(LiveActivity.user == user)
        if runningSession:
            return "You already have a manual activity running, stop it first."

        # get last used platform, or fallback to default
        platform = last_platform_for_game(user=user, game=game)
        if not platform:
            self.logger.debug("No last platform found, using default platform")
            platform = user.default_platform

        timestamp = tpbackend.utils.now()
        LiveActivity.create(user=user, game=game, platform=platform, started=timestamp)
        return f"⏱️ Started playing *{game.name}*. Send `!stop` when you are done."
