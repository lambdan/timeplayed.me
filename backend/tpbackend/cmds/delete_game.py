from tpbackend import api
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game


class DeleteGameCommand(AdminCommand):
    def __init__(self):
        names = ["delete_game", "del_game", "remove_game"]
        d = "Delete game"
        h = f"Usage: `!{names[0]} <game_id>` to preview, `!{names[0]} <game_id> confirm` to delete"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        parts = msg.split()
        game_id = int(parts[0])
        confirmed = len(parts) > 1 and parts[1].lower() == "confirm"

        game = Game.get_or_none(Game.id == game_id)  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        activities = api.get_activities(game=game_id)
        if activities.total > 0:
            return f"Error: game ({game.name}) has activities"

        year = game.release_year if game.release_year else "Unknown"
        if not confirmed:
            return (
                f"Are you sure you want to delete *{game.name}* ({year})?\n"
                f"Type `!delete_game {game_id} confirm` to confirm."
            )

        name = str(game.name)
        game.delete_instance()
        return f"Game *{name}* ({year}) deleted"
