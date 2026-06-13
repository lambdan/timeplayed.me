from tpbackend.game.select import GameSelect
from .admin_command import AdminCommand
from tpbackend.storage import User


class SetParentCommand(AdminCommand):
    def __init__(self):
        names = ["set_parent"]
        d = "Set parent ID for game"
        h = f"Usage: `!{names[0]} <game_id> <parent_game_id>`. Use null to clear."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip().lower()
        parent_id = splitted[1].strip().lower()

        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."

        if parent_id == "null":
            try:
                game.set_parent(None)
                game.save()
                return f"Parent of game '{game.get_name()}' cleared."
            except Exception as e:
                return f"Error clearing parent: {str(e)}"

        parent = GameSelect.by_id(parent_id)
        if not parent:
            return f"Error: Parent game with id {parent_id} not found."

        try:
            game.set_parent(parent)
            game.save()
            return f"Game '{game.get_name()}' is now child of '{parent.get_name()}'"
        except Exception as e:
            return f"Error setting parent: {str(e)}"
