from tpbackend.game.select import GameSelect
from .admin_command import AdminCommand
from tpbackend.storage import User
from tpbackend.storage import Game
from tpbackend.sgdb.controller import get_game_by_id
from tpbackend.operations import adopt_name


class SetSGDBIDAdminCommand(AdminCommand):
    def __init__(self):
        names = ["set_sgdb_id", "set_sgdb", "sgdb"]
        d = "Set SGDB ID for game"
        h = f"Usage: `!{names[0]} <game_id> <sgdb_id>`. Use null for sgdb_id to clear."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        sgdb_id = None
        if splitted[1].strip().lower() != "null":
            sgdb_id = int(splitted[1].strip())
        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."

        # if game.sgdb_id == sgdb_id:
        #    return "Already set!"

        # any game that already has this sgdb_id?
        # (special case for 0, multiple games can have sgdb_id 0, its for games that are not in SGDB)
        # (None/null means the game is missing SGDB id, so also multiple games can have that)
        if sgdb_id != 0 and sgdb_id is not None:
            existing_game = Game.get_or_none(Game.sgdb_id == sgdb_id)  # type: ignore
            if existing_game and existing_game.id != game.id:
                return f"Error: SGDB ID {sgdb_id} is already assigned to '{existing_game.get_label()}' (id: {existing_game.id})"  # type: ignore

        if sgdb_id == 0 or sgdb_id is None:
            game.set_sgdb_id(sgdb_id)
            game.save()
            return f"{game.get_label()} - SGDB ID set to: {game.sgdb_id}"

        # get info from sgdb
        sgdb_game = get_game_by_id(sgdb_id)
        if not sgdb_game:
            return f"Error: No game found in SGDB with id {sgdb_id}."
        if not sgdb_game.name:
            return f"Error: SGDB game with id {sgdb_id} has no name."

        out, conflict = adopt_name(game, sgdb_game.name, "SGDB")
        if conflict:
            return out + "\n - ABORTING!"

        if sgdb_game.release_date:
            year = sgdb_game.release_date.year
            if year != game.get_release_year():
                game.set_release_year(year)
                out += f"- Release year set to {year}\n"

        game.set_sgdb_id(sgdb_id)
        game.save()
        out += f"OK, SGDB ID updated for *{game.get_label()}*"
        return out
