from typing import cast
from tpbackend.game.select import GameSelect
from tpbackend.igdb.controller import get_game_info
from tpbackend.storage import User
from tpbackend.utils2 import ts_to_dt
from .command import Command
from tpbackend.storage import Game
from tpbackend.sgdb.controller import get_game_by_id


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
            return f"Error: Game with IGDB ID {igdb_id} already exists in the database (id: {game_by_igdb_id.id}, name: {game_by_igdb_id.name})"

        igdb_game = get_game_info(igdb_id)
        if not igdb_game:
            return f"Error: did not find game on IGDB with id {igdb_id}"

        game_year = None
        if igdb_game.first_release_date:
            dt = ts_to_dt(igdb_game.first_release_date)
            game_year = dt.year

        #        # Check whether a game with the same name already exists.  Two games
        #        # may share a name (e.g. a 2005 and a 2023 release of the same title),
        #        # but only when both have a release_year set so they can be told apart.
        #        ex_game = GameSelect.by_name_or_alias(igdb_game.name)
        #        if ex_game:
        #            if not game_year:
        #                return (
        #                    f"Error: Game with name *{sgdb_game.name}* already exists in the database "
        #                    f"(id: {ex_game.id}, name: {ex_game.name}). "  # type: ignore
        #                    "SGDB reports no release year for this game, so it cannot be added as a separate entry."
        #                )
        #            if not ex_game.release_year:  # type: ignore
        #                return (
        #                    f"Error: Game with name *{sgdb_game.name}* already exists in the database "
        #                    f"(id: {ex_game.id}, name: {ex_game.name}) but has no release year set. "  # type: ignore
        #                    f"Please set its release year first (`!sgry {ex_game.id} <year>`)."  # type: ignore
        #                )
        #            # Check for a true duplicate: same name AND same year already in DB.
        #            true_duplicate = Game.get_or_none(  # type: ignore
        #                (Game.name == sgdb_game.name) & (Game.release_year == game_year)  # type: ignore
        #            )
        #            if true_duplicate:
        #                return (
        #                    f"Error: Game *{sgdb_game.name}* ({game_year}) already exists in the database "
        #                    f"(id: {true_duplicate.id}, name: {true_duplicate.name})."  # type: ignore
        #                )

        new_game = Game.create(name=igdb_game.name, igdb_id=igdb_id, release_year=game_year)  # type: ignore
        new_game = cast(Game, new_game)
        new_game.add_history(f"Game added by SGDB ID by user {user.get_id()}")
        new_game.save()

        out = "✅ Added game by SGDB id!\n"
        out += f"- *{new_game.name}*\n"
        out += f"- Year: {game_year}\n"
        out += f"- SGDB ID: {new_game.sgdb_id}\n"
        out += f"- Game ID: {new_game.id}"

        return out
