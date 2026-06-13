from tpbackend.storage.storage_v2 import Platform, User, Game
from tpbackend.cmds.admin_command import AdminCommand


class RefreshSearch(AdminCommand):
    def __init__(self):
        names = ["refs", "rs"]
        d = "Refresh all search columns"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        for game in Game.select():
            game.save()  # triggers reindex
        for user in User.select():
            user.save()  # triggers reindex
        for platform in Platform.select():
            platform.save()  # triggers reindex
        return "Done"
