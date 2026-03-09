from tpbackend import api
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game
from tpbackend.utils import game_name


class DeleteGameCommand(AdminCommand):
    def __init__(self):
        names = ["delete_game", "del_game", "remove_game"]
        d = "Delete game"
        h = f"Usage: `!{names[0]} <game_id>` to preview, `!{names[0]} <game_id> y` to delete"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        parts = msg.split()
        game_id = int(parts[0])
        confirmed = len(parts) > 1 and parts[1].lower() == "y"

        game = Game.get_or_none(Game.id == game_id)  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        activities = api.get_activities(game=game_id)
        if activities.total > 0:
            return f"Error: game ({game.name}) has activities"

        name = game_name(game)
        if not confirmed:
            return (
                f"Are you sure you want to delete *{name}*?\n"
                f"Run the command again with `y` at the end to confirm."
            )

        game.delete_instance()
        return f"Game *{name}* deleted"
