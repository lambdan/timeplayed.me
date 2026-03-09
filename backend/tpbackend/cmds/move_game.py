from tpbackend.cmds.command import Command
from tpbackend.cmds.set_game import set_game_actually
from tpbackend.storage.storage_v2 import Activity, Game, User


class MoveGameCommand(Command):
    def __init__(self):
        names = ["move_game", "mg"]
        d = "Move all activities of a game to another game"
        h = f"""
Move all your activities from one game to another.

Usage: `!{names[0]} <from_game_id> <to_game_id>`
Example: move all your game 4 activities into game 35:
```
!{names[0]} 4 35
```

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        from_game_id = splitted[0].strip()
        to_game_id = splitted[1].strip()

        try:
            from_game = Game.get_or_none(Game.id == int(from_game_id))  # type: ignore
        except ValueError:
            return (
                f"Error: Invalid game ID '{from_game_id}'. Please provide a numeric ID."
            )
        if not from_game:
            return f"Error: Game with id {from_game_id} not found."

        try:
            to_game = Game.get_or_none(Game.id == int(to_game_id))  # type: ignore
        except ValueError:
            return (
                f"Error: Invalid game ID '{to_game_id}'. Please provide a numeric ID."
            )
        if not to_game:
            return f"Error: Game with id {to_game_id} not found."

        activities = list(
            Activity.select().where(  # type: ignore
                Activity.game == from_game,
                Activity.user == user,
            )
        )
        if not activities:
            return (
                f"No activities found for game {from_game.name} (id: {from_game_id})."
            )

        for act in activities:
            set_game_actually(act, to_game)

        return f"Moved {len(activities)} activit{'y' if len(activities) == 1 else 'ies'} from *{from_game.name}* to *{to_game.name}*."
