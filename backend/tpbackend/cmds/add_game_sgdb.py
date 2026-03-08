from tpbackend import steamgriddb
from tpbackend.operations import get_game_by_name_or_alias
from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Game


class AddGameSGDBCommand(Command):
    def __init__(self):
        names = ["add_sgdb", "ag_sgdb"]
        d = "Add game (by SteamGridDB ID)"
        h = """
Add a new game to the database by providing SteamGridDB ID

Usage: `!add_sgdb <sgdb_id>`
Example (adding Pokemon Blue): ```
!add_sgdb 35291
```
Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        msg = msg.strip()
        if msg == "":
            return f"No SteamGridDB ID provided? Try `!help {self.names[0]}` for help"
        try:
            sgdb_id = int(msg)
        except Exception:
            return "Error: Invalid id"

        if sgdb_id <= 0:
            return "Error: Invalid id (must be > 0). 0 is used for games that are NOT on SGDB."

        game_by_sgdb_id = Game.get_or_none(Game.sgdb_id == sgdb_id)  # type: ignore
        if game_by_sgdb_id:
            return f"Error: Game with SteamGridDB ID {sgdb_id} already exists in the database (id: {game_by_sgdb_id.id}, name: {game_by_sgdb_id.name})"  # type: ignore

        sgdb_game = steamgriddb.get_game_by_id(sgdb_id)
        if not sgdb_game:
            return f"Error: did not find game on SGDB with id {sgdb_id}"
        if not sgdb_game.name:
            return "Error: SGDB has no name for that game"

        game_year = (sgdb_game.release_date and sgdb_game.release_date.year) or None

        # Check whether a game with the same name already exists.  Two games
        # may share a name (e.g. a 2005 and a 2023 release of the same title),
        # but only when both have a release_year set so they can be told apart.
        ex_game = get_game_by_name_or_alias(sgdb_game.name)  # type: ignore
        if ex_game:
            if not game_year:
                return (
                    f"Error: Game with name *{sgdb_game.name}* already exists in the database "
                    f"(id: {ex_game.id}, name: {ex_game.name}). "  # type: ignore
                    "SGDB reports no release year for this game, so it cannot be added as a separate entry."
                )
            if not ex_game.release_year:  # type: ignore
                return (
                    f"Error: Game with name *{sgdb_game.name}* already exists in the database "
                    f"(id: {ex_game.id}, name: {ex_game.name}) but has no release year set. "  # type: ignore
                    f"Please set its release year first (`!sgry {ex_game.id} <year>`)."  # type: ignore
                )
            # Check for a true duplicate: same name AND same year already in DB.
            true_duplicate = Game.get_or_none(  # type: ignore
                (Game.name == sgdb_game.name) & (Game.release_year == game_year)  # type: ignore
            )
            if true_duplicate:
                return (
                    f"Error: Game *{sgdb_game.name}* ({game_year}) already exists in the database "
                    f"(id: {true_duplicate.id}, name: {true_duplicate.name})."  # type: ignore
                )

        new_game = Game.create(name=sgdb_game.name, sgdb_id=sgdb_id, release_year=game_year)  # type: ignore
        out = "✅ Added game by SGDB id!\n"
        out += f"- *{new_game.name}*\n"
        out += f"- Year: {game_year}\n"
        out += f"- SGDB ID: {new_game.sgdb_id}\n"
        out += f"- Game ID: {new_game.id}"
        return out
