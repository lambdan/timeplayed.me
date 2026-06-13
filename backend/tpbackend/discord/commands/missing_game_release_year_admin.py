from typing import cast
from tpbackend.storage import User, Game
from .admin_command import AdminCommand


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
            game = cast(Game, game)
            count += 1
            out += f"- **{game.get_id()}** - {game.get_name()}\n"
            if len(out) > 1337:
                out += f"... and {missing.count() - count} more"
                break
        return out
