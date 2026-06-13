import datetime
from tpbackend.game.select import GameSelect
from tpbackend.utils2 import ts_to_dt
from .admin_command import AdminCommand
from tpbackend.storage import User
from .set_sgdb_id import SetSGDBIDCommand
from tpbackend.sgdb.controller import search


class AutoSGDBAdminCommand(AdminCommand):
    def __init__(self):
        names = ["auto_sgdb", "asgdb"]
        d = "Automatically set SGDB for a game"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        game_id = int(splitted[0].strip())
        confirmed = len(splitted) > 1 and splitted[1].strip().lower() == "y"
        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."

        sgdb_games = search(query=game.get_name())
        if len(sgdb_games) == 0:
            return "Error: no SGDB games found"

        best_match = sgdb_games[0]

        # if game.sgdb_id == best_match.id:
        #    return "Best matching SGDB ID is already set!"

        if not confirmed:
            rd = ts_to_dt(best_match.release_date) if best_match.release_date else None
            year = rd.year if rd else "?"
            out = ""
            out += f"Best SGDB match for '{game.get_name()}'\nis\n'{best_match.name}' ({year}) (id: {best_match.id}).\n"
            out += "\nIf this is correct, run the command again with `y` at the end to confirm."
            return out

        return SetSGDBIDCommand().execute(user, f"{game_id} {best_match.id}")
