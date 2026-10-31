from tpbackend.game.select import GameSelect
from tpbackend.game.utils import game_label
from tpbackend.operations import merge_aliases, merge_games
from tpbackend.storage import Activity, Game, User
from .admin_command import AdminCommand


def _aliases_text(aliases: list[str]) -> str:
    return ", ".join(f"`{a}`" for a in aliases)


def merge_preview(source: Game, target: Game) -> str:
    """what merging source into target would do, shared with the igdb command"""
    count = Activity.select().where(Activity.game == source).count()  # type: ignore
    aliases = merge_aliases(source, target)
    out = (
        f"This will merge *{game_label(source)}* (id: {source.get_id()}) into "
        f"*{game_label(target)}* (id: {target.get_id()}): {count} activities are moved"
    )
    if aliases:
        out += f", {_aliases_text(aliases)} added as alias"
    out += f" and game {source.get_id()} is deleted.\n"
    out += "Run the command again with `y` at the end to confirm."
    return out


def merge_and_report(source: Game, target: Game) -> str:
    label = game_label(source)
    aliases = merge_aliases(source, target)
    moved = merge_games(source, target)
    out = f"Merged *{label}* into *{game_label(target)}* ({moved} activities moved"
    if aliases:
        out += f", {_aliases_text(aliases)} added as alias"
    return out + ")"


class MergeGameAdminCommand(AdminCommand):
    def __init__(self):
        names = ["merge", "merge_game"]
        d = "Merge a game into another game"
        h = f"""
Merge a duplicate game into another: all its activities (all users) are moved over, its name and aliases are kept as aliases, and it's deleted.

Usage: `!{names[0]} <from_game_id> <into_game_id> [y]`
Example: merge game 5 into game 3:
```
!{names[0]} 5 3
```
Shows what will happen, run it again with `y` at the end to do it.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        parts = msg.split()
        if len(parts) not in (2, 3):
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        confirmed = len(parts) == 3 and parts[2].lower() == "y"

        try:
            source = GameSelect.by_id(int(parts[0]))
            target = GameSelect.by_id(int(parts[1]))
        except ValueError:
            return "Error: game IDs have to be numbers."
        if not source:
            return f"Error: Game with id {parts[0]} not found."
        if not target:
            return f"Error: Game with id {parts[1]} not found."
        if source.get_id() == target.get_id():
            return "Error: can't merge a game into itself."

        if not confirmed:
            return merge_preview(source, target)
        return merge_and_report(source, target)
