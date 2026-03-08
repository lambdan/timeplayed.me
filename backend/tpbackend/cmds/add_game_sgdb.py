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
            return f"Error: Game with SteamGridDB ID {sgdb_id} already exists in the database (id: {game_by_sgdb_id.id})"  # type: ignore

        game = steamgriddb.get_game_by_id(sgdb_id)
        if not game:
            return f"Error: did not find game on SGDB with id {sgdb_id}"
        if not game.name:
            return "Error: SGDB has no name for that game"

        # check if it exists by name
        existing_game_name = get_game_by_name_or_alias(game.name)  # type: ignore
        if existing_game_name:
            return f"Error: Game with name *{game.name}* already exists in the database (id: {existing_game_name.id})"  # type: ignore

        game_year = (game.release_date and game.release_date.year) or None
        new_game = Game.create(name=game.name, sgdb_id=sgdb_id, release_year=game_year)  # type: ignore
        out = "✅ Added game by SGDB id!\n"
        out += f"- *{new_game.name}*\n"
        out += f"- Year: {game_year}\n"
        out += f"- SGDB ID: {new_game.sgdb_id}\n"
        out += f"- Game ID: {new_game.id}"
        return out
