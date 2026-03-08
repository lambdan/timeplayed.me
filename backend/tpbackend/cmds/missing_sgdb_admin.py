from tpbackend.storage.storage_v2 import User, Game
from tpbackend.cmds.admin_command import AdminCommand


class MissingSGDBAdminCommand(AdminCommand):
    def __init__(self):
        names = ["missing_sgdb", "msgdb"]
        d = "Get list of games missing SGDB id"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        missing = Game.select().where(Game.sgdb_id.is_null())  # type: ignore
        if len(missing) == 0:
            return "All games have SGDB id! 🥳"
        count = 0
        out = ""
        for game in missing:
            out += f"- {game.name} (id: {game.id})\n"  # type: ignore
            if count > 50 or len(out) > 1337:
                out += f"... and {missing.count() - count} more"
                break
        return out
