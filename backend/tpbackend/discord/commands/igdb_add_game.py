from tpbackend.igdb.controller import get_or_create_game
from tpbackend.storage import User
from .command import Command
from tpbackend.storage import Game


class AddGameIGDBCommand(Command):
    def __init__(self):
        names = ["add_igdb"]
        d = "Add game (by IGDB ID)"
        h = """
Add a new game to the database by providing IGDB ID

Usage: `!add_igdb <igdb_id>`
Example (adding GTA San Andreas): ```
!add_igdb 732
```
Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        msg = msg.strip()
        if msg == "":
            return f"No ID provided? Try `!help {self.names[0]}` for help"
        try:
            igdb_id = int(msg)
        except Exception:
            return "Error: Invalid id"

        if igdb_id <= 0:
            return "Error: Invalid id (must be > 0). 0 is used for games that are NOT on IGDB."

        game_by_igdb_id = Game.get_or_none(Game.igdb_id == igdb_id)
        if game_by_igdb_id:
            return f"Error: Game already exists in the database (id: {game_by_igdb_id.id}, name: {game_by_igdb_id.name})"

        new_game = get_or_create_game(igdb_id)
        if not new_game:
            return "Error: game not added, probably invalid id?"

        new_game.add_history(f"Game added by IGDB ID by user {user.get_id()}")
        new_game.save()

        out = "✅ Added game by IGDB id!\n"
        out += f"- *{new_game.name}*\n"
        out += f"- Year: {new_game.get_release_year()}\n"
        out += f"- Game ID: {new_game.id}"

        return out
