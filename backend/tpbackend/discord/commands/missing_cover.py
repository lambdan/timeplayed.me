from tpbackend.storage import User, Game
from .admin_command import AdminCommand
from typing import cast


class MissingCoverAdminCommand(AdminCommand):
    def __init__(self):
        names = ["missing_cover", "mc"]
        d = "Get list of games missing cover art"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        missing = []
        for game in Game.select():
            game = cast(Game, game)
            if game.has_cover_art():
                continue
            missing.append(game)

        if len(missing) == 0:
            return "All games have cover art! :D"
        count = 0
        out = ""
        for game in missing:
            game = cast(Game, game)
            count += 1
            out += f"- **{game.get_id()}** - {game.get_name()}\n"
            if count > 20 or len(out) > 1337:
                out += f"... and {len(missing) - count} more\n"
                break
        return out
