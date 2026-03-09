from typing import Optional

from tpbackend.cmds.command import Command
from tpbackend.cmds.set_game import set_game_actually
from tpbackend.storage.storage_v2 import Activity, Game, User


def execute_move_game(
    msg: str, cmd_name: str, user_filter: Optional[User] = None
) -> str:
    """Shared implementation for move_game and adm_move_game.

    When *user_filter* is provided only activities belonging to that user are
    considered; when it is ``None`` activities for all users are affected.
    """
    splitted = msg.split(" ")
    if len(splitted) < 2:
        return f"Invalid syntax. See `!help {cmd_name}` for help."
    from_game_id = splitted[0].strip()
    to_game_id = splitted[1].strip()
    confirmed = len(splitted) >= 3 and splitted[2].strip().lower() == "y"

    try:
        from_game = Game.get_or_none(Game.id == int(from_game_id))  # type: ignore
    except ValueError:
        return f"Error: Invalid game ID '{from_game_id}'. Please provide a numeric ID."
    if not from_game:
        return f"Error: Game with id {from_game_id} not found."

    try:
        to_game = Game.get_or_none(Game.id == int(to_game_id))  # type: ignore
    except ValueError:
        return f"Error: Invalid game ID '{to_game_id}'. Please provide a numeric ID."
    if not to_game:
        return f"Error: Game with id {to_game_id} not found."

    where_clause = [Activity.game == from_game]  # type: ignore
    if user_filter is not None:
        where_clause.append(Activity.user == user_filter)  # type: ignore

    activities = list(Activity.select().where(*where_clause))  # type: ignore
    if not activities:
        return f"No activities found for game {from_game.name} (id: {from_game_id})."

    count = len(activities)
    noun = "activity" if count == 1 else "activities"

    if not confirmed:
        return (
            f"This will move {count} {noun} from *{from_game.name}* to *{to_game.name}*.\n"
            f"Run the command again with `y` at the end to confirm."
        )

    for act in activities:
        set_game_actually(act, to_game)

    return f"Moved {count} {noun} from *{from_game.name}* to *{to_game.name}*."


class MoveGameCommand(Command):
    def __init__(self):
        names = ["move_game", "mg"]
        d = "Move all activities of a game to another game"
        h = f"""
Move all your activities from one game to another.

Usage: `!{names[0]} <from_game_id> <to_game_id> [y]`
Example: move all your game 4 activities into game 35:
```
!{names[0]} 4 35
```

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        return execute_move_game(msg, self.names[0], user_filter=user)
