import datetime
from tpbackend.discord.commands.igdb_set_id import SetIGDBIDCommand
from tpbackend.game.select import GameSelect
from tpbackend.igdb.controller import search_game
from tpbackend.utils2 import ts_to_dt
from .admin_command import AdminCommand
from tpbackend.storage import User


class AutoIGDBAdminCommand(AdminCommand):
    def __init__(self):
        names = ["auto_igdb", "aigdb"]
        d = "Automatically set IGDB for a game"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        game_id = int(splitted[0].strip())
        confirmed = len(splitted) > 1 and splitted[1].strip().lower() == "y"
        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."

        igdb_games = search_game(query=game.get_name())
        if len(igdb_games) == 0:
            return "Error: no SGDB games found"

        best_match = igdb_games[0]

        if not confirmed:
            rd = None
            if best_match.first_release_date:
                rd = ts_to_dt(best_match.first_release_date)
            year = rd.year if rd else "?"
            out = ""
            out += f"Best SGDB match for '{game.get_name()}'\nis\n'{best_match.name}' ({year}) (id: {best_match.id}).\n"
            out += "\nIf this is correct, run the command again with `y` at the end to confirm."
            return out

        return SetIGDBIDCommand().execute(user, f"{game_id} {best_match.id}")  # haaax
