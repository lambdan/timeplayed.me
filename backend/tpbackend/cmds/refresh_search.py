from tpbackend.storage.storage_v2 import User, Game
from tpbackend.cmds.admin_command import AdminCommand


class RefreshSearch(AdminCommand):
    def __init__(self):
        names = ["refs", "rs"]
        d = "Refresh all search columns"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        games = Game.select()
        for game in games:
            game.save()  # triggers reindex
        return "Done"
