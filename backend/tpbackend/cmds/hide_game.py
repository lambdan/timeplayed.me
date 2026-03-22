from tpbackend.storage.storage_v2 import Game_or_none, User
from tpbackend.cmds.admin_command import AdminCommand


class HideGameCommand(AdminCommand):
    def __init__(self):
        names = ["hide_game", "hg"]
        d = "Toggle hidden state of game"
        h = "Toggles hidden state of game"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game = Game_or_none(int(msg))
        if not game:
            return f"Error: Game with id {msg} not found."
        game.set_hidden(not game.get_hidden())
        state = "hidden" if game.get_hidden() else "visible"
        return f"Game '{game.name}' is now {state}"
