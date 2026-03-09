from tpbackend.storage.storage_v2 import User, Game
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.utils import game_name


class MissingGRYAdminCommand(AdminCommand):
    def __init__(self):
        names = ["missing_gry", "mgry"]
        d = "Get list of games missing release year"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        missing = Game.select().where(Game.release_year.is_null())
        if len(missing) == 0:
            return "All games have a release year!"
        count = 0
        out = ""
        for game in missing:
            count += 1
            out += f"- **{game.id}** - {game_name(game)}\n"  # type: ignore
            if len(out) > 1337:
                out += f"... and {missing.count() - count} more"
                break
        return out
