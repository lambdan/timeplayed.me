from tpbackend.game.select import GameSelect
from tpbackend.operations import sync_activities_hidden
from tpbackend.storage import User
from .admin_command import AdminCommand


class HideGameAdminCommand(AdminCommand):
    def __init__(self):
        names = ["hide_game", "hg"]
        d = "Toggle hidden state of game"
        h = "Toggles hidden state of game"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game = GameSelect.by_id(int(msg))
        if not game:
            return f"Error: Game with id {msg} not found."
        game.set_hidden(not game.get_hidden())
        game.save()
        state = "hidden" if game.get_hidden() else "visible"
        affected_activities = sync_activities_hidden(game)
        return f"Game '{game.get_label()}' is now {state}. {affected_activities} activities updated hidden state."
