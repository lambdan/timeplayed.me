from tpbackend.activity.query import ActivityQuery
from tpbackend.game.select import GameSelect
from .admin_command import AdminCommand
from tpbackend.storage import User


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

        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."

        activities = ActivityQuery.base(include_hidden=True)
        activities = ActivityQuery.game(activities, game_id)
        if ActivityQuery.count(activities) > 0:
            return f"Error: game ({game.get_name()}) has activities"

        name = game.get_name()
        if not confirmed:
            return (
                f"Are you sure you want to delete *{name}*?\n"
                f"Run the command again with `y` at the end to confirm."
            )

        game.delete_instance()
        return f"Game *{name}* deleted"
