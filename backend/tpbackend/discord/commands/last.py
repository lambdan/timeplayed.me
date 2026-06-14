from tpbackend.activity.query import ActivityQuery
from tpbackend.activity.utils import md_activity_link
from tpbackend.game.utils import md_game_link
from tpbackend.platform.utils import display_name
from tpbackend.storage import User
from .command import Command
from typing import cast

from tpbackend.storage import Activity
from tpbackend.utils2 import js_iso, secsToHHMMSS

TOO_LONG_ERR = "Output too long for Discord. Try with a smaller number."


class LastActivityCommand(Command):
    def __init__(self):
        names = ["last", "l"]
        d = "Get last activity"
        h = """
Gets your last activity: `!last`

Get your last n activities: `!last n`
"""
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        amount = 1 if msg == "" else int(msg)
        amount = max(1, amount)
        amount = min(100, amount)
        activities = self.get_activities(user, amount)
        if len(activities) == 0:
            return "No activities found."
        activities = reversed(activities)  # newest at the bottom
        return self.new_output(activities)

    def get_activities(self, user: User, amount: int) -> str:
        q = ActivityQuery.base()
        q = ActivityQuery.user(q, user)
        q = ActivityQuery.apply_sort(q, "timestamp", "desc")
        q = q.limit(amount)
        return q

    def new_output(self, activities) -> str:
        out = ""
        for act in activities:
            act = cast(Activity, act)
            ts = js_iso(act.get_datetime())
            out += md_activity_link(act) + "\n"
            out += f"- {md_game_link(act.get_game())}\n"
            out += f"- {display_name(act.get_platform())}"
            if act.emulated:
                out += " (emu)"
            out += "\n"
            out += f"- {ts} UTC\n"
            out += f"- {secsToHHMMSS(act.get_seconds())}\n"
            out += "\n"
            if len(out) >= 2000:
                return TOO_LONG_ERR
        return out.strip()
