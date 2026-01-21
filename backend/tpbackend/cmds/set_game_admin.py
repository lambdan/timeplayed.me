from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Game, Activity
from tpbackend.cmds.set_game import set_game_actually


class SetGameAdminCommand(AdminCommand):
    def __init__(self):
        names = ["adm_set_game", "asg"]
        d = "Set game of activity"
        h = """
        See regular `!set_game` for usage
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        activities = splitted[0].split(",")
        game_id = splitted[1].strip()
        return self.set_game(user, activities, game_id)

    def set_game(self, user: User, activity_ids: list[str], game_id: str) -> str:
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        msg = ""
        for activity_id in activity_ids:
            act = Activity.get_or_none(Activity.id == int(activity_id))  # type: ignore
            if not act:
                msg += f"- {activity_id}: ❌ not found\n"
                continue
            msg += f"- {activity_id}: {set_game_actually(act, game)}\n"
        return msg
