from tpbackend import api
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game


class DeleteGameCommand(AdminCommand):
    def __init__(self):
        names = ["delete_game", "del_game", "remove_game"]
        d = "Delete game"
        h = f"Usage: `!{names[0]} <game_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game_id = int(msg)
        game = Game.get_or_none(Game.id == game_id)  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        activities = api.get_activities(game=game_id)
        if activities.total > 0:
            return f"Error: game ({game.name}) has activities"
        name = str(game.name)
        game.delete_instance()
        return f"Game *{name}* deleted"
