from tpbackend.storage import (
    User,
    Activity_or_none,
)
from .command import Command
from tpbackend.utils import game_name, activity_name
from tpbackend.utils2 import js_iso, secsToHHMMSS


class GetActivityCommand(Command):
    def __init__(self):
        names = ["get_activity", "ga"]
        d = "Get an activity"
        h = "Get an activity by ID\nUsage: `!get_activity <activity_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        activity = Activity_or_none(int(msg), include_hidden=True)

        if not activity:
            return f"Error: Activity with id {msg} not found."

        if activity.get_hidden():
            # only show for admins or self
            if (
                not self.is_admin(user)
                and activity.get_user().get_id() != user.get_id()
            ):
                return f"Error: Activity with id {msg} not found."

        formatted_duration = secsToHHMMSS(activity.get_seconds())
        msg = ""
        msg += f"{activity_name(activity, as_markdown_link=True)}\n"
        msg += f"- User: {activity.get_user().get_name()}\n"
        msg += f"- Game: {game_name(activity.get_game(), as_markdown_link=True)}\n"
        msg += f"- Platform: *{activity.get_platform().get_display_name()}*"
        if activity.get_emulated():
            msg += " (Emulated)"
        msg += "\n"
        msg += f"- Date: {js_iso(activity.get_datetime())}\n"
        msg += f"- Duration: {formatted_duration}\n"
        msg += f"- Created: {js_iso(activity.get_created())}\n"
        msg += f"- Updated: {js_iso(activity.get_updated())}\n"

        if activity.get_hidden():
            msg += "- **This activity is hidden**\n"

        if self.is_admin(user):
            msg += "# History\n"
            if len(activity.get_history()) == 0:
                msg += "No history\n"
            else:
                msg += "```"
                for h in activity.get_history():
                    msg += h + "\n"
                msg += "```"

        return msg.strip()
