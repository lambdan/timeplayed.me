from tpbackend.storage.storage_v2 import Platform, User, Activity, Game
from tpbackend.cmds.command import Command
from tpbackend import api, utils


class GetActivityCommand(Command):
    def __init__(self):
        names = ["get_activity", "ga"]
        d = "Get an activity"
        h = "Get an activity by ID\nUsage: `!get_activity <activity_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        activity = Activity.get_or_none(Activity.id == int(msg))  # type: ignore
        if not activity:
            return f"Error: Activity with id {msg} not found."
        user = User.get_or_none(User.id == activity.user_id)  # type: ignore
        game = Game.get_or_none(Game.id == activity.game_id)  # type: ignore
        platform = Platform.get_or_none(Platform.id == activity.platform_id)  # type: ignore
        formatted_duration = utils.secsToHHMMSS(activity.seconds)
        msg = ""
        msg += f"## Activity {activity.id}\n"
        msg += f"- User: *{user.name}*\n"
        msg += f"- Game: *{game.name}*\n"
        msg += f"- Platform: *{platform.name or platform.abbreviation}*\n"
        msg += f"- Date: {activity.timestamp}\n"
        msg += f"- Duration: {formatted_duration}\n"
        return msg.strip()
