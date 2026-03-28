from tpbackend.storage.storage_v2 import (
    User,
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
        formatted_duration = utils.secsToHHMMSS(activity.get_seconds())
        formatted_dt = activity.get_datetime().strftime("%Y-%m-%d %H:%M:%S UTC")
        msg = ""
        msg += f"{activity_name(activity, as_markdown_link=True)}\n"
        msg += f"- User: {activity.get_user().get_name()}\n"
        msg += f"- Game: {game_name(activity.get_game(), as_markdown_link=True)}\n"
        msg += f"- Platform: *{activity.get_platform().get_display_name()}*\n"
        msg += f"- Date: {formatted_dt}\n"
        msg += f"- Duration: {formatted_duration}\n"
        return msg.strip()
