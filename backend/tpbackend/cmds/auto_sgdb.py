import datetime
from tpbackend import steamgriddb
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.operations import get_game_by_name_or_alias
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game
from tpbackend.cmds.set_sgdb_id import SetSGDBIDCommand


class AutoSGDBAdminCommand(AdminCommand):
    def __init__(self):
        names = ["auto_sgdb", "asgdb"]
        d = "Automatically set SGDB for a game"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        game_id = int(splitted[0].strip())
        confirmed = len(splitted) > 1 and splitted[1].strip().lower() == "y"

        game_name = Game.get_or_none(Game.id == game_id).name  # type: ignore
        if not game_name:
            return f"Error: Game with id {game_id} not found."

        sgdb_game = steamgriddb.search(query=game_name)
        if len(sgdb_game) == 0:
            return f"Error: no SGDB games found"

        best_match = sgdb_game[0]
        if not confirmed:
            year = (
                datetime.datetime.utcfromtimestamp(best_match.release_date).year
                if best_match.release_date
                else "?"
            )
            out = ""
            out += f"Best SGDB match for '{game_name}'\nis\n'{best_match.name}' ({year}) (id: {best_match.id}).\n"
            out += "\nIf this is correct, run the command again with `y` at the end to confirm."
            return out

        set_command = SetSGDBIDCommand()
        return set_command.execute(user, f"{game_id} {best_match.id}")
