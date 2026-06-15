from tpbackend.game.select import GameSelect
from .admin_command import AdminCommand
from tpbackend.storage import User


class SetSGDBGridIDCommand(AdminCommand):
    def __init__(self):
        names = ["set_grid_id", "sgid"]
        d = "Set SGDB Grid ID for game"
        h = f"Usage: `!{names[0]} <game_id> <grid_id>`. Use null as grid to unset."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        grid_id = None
        if splitted[1].strip().lower() != "null":
            grid_id = int(splitted[1].strip())
        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."
        game.set_sgdb_grid_id(grid_id)
        game.save()
        return f"{game.name} - SGDB GRID ID set to: {game.sgdb_grid_id}"
