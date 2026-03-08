from tpbackend import api
from tpbackend.storage.storage_v2 import User, Game
from tpbackend.cmds.admin_command import AdminCommand


class GamesWithoutActivityAdminCommand(AdminCommand):
    def __init__(self):
        names = ["games_without_activity", "gwa"]
        d = "Get list of games that have no activity"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        games = Game.select()
        games_without_activity = []
        for game in games:
            activities = api.get_activities(game=game.id, limit=1)
            if activities.total == 0:
                games_without_activity.append(game)

        if len(games_without_activity) == 0:
            return "All games have activity!"

        count = 0
        out = ""
        for game in games_without_activity:
            count += 1
            out += f"- **{game.id}** - {game.name}\n"  # type: ignore
            if count >= 50 or len(out) >= 1500:
                remaining = len(games_without_activity) - count
                if remaining > 0:
                    out += f"... and {remaining} more"
                break
        return out
