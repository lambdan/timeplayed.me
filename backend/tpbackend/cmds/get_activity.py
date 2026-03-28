from tpbackend.storage.storage_v2 import (
    Platform,
    User,
    Game,
    Activity_or_none,
)
from tpbackend.cmds.command import Command
from tpbackend.utils import game_name, activity_name
from tpbackend import utils


class GetActivityCommand(Command):
    def __init__(self):
        names = ["get_activity", "ga"]
        d = "Get an activity"
        h = "Get an activity by ID\nUsage: `!get_activity <activity_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        activity = Activity_or_none(int(msg))
        if not activity:
            return f"Error: Activity with id {msg} not found."
        user = User.get_or_none(User.id == activity.user_id)  # type: ignore
        game = Game.get_or_none(Game.id == activity.game_id)  # type: ignore
        platform = Platform.get_or_none(Platform.id == activity.platform_id)  # type: ignore
        formatted_duration = utils.secsToHHMMSS(activity.get_seconds())
        formatted_dt = activity.get_datetime().strftime("%Y-%m-%d %H:%M:%S UTC")
        msg = ""
        msg += f"{activity_name(activity, as_markdown_link=True)}\n"
        msg += f"- User: {user.name}\n"
        msg += f"- Game: {game_name(game, as_markdown_link=True)}\n"
        msg += f"- Platform: *{platform.name or platform.abbreviation}*\n"
        msg += f"- Date: {formatted_dt}\n"
        msg += f"- Duration: {formatted_duration}\n"
        return msg.strip()
