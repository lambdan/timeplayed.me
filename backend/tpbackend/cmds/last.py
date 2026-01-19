from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Activity
from tpbackend import utils


class LastActivityCommand(Command):
    def __init__(self):
        names = ["last", "l"]
        d = "Get last activity"
        h = """
Gets your last activity: `!last`

Get your last n activities: `!last n`

Because of Discord message length limits, n is capped at 10.
"""
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        amount = 1 if msg == "" else int(msg)
        amount = max(1, amount)
        amount = min(10, amount)
        return self.get_activities(user, amount)

    def get_activities(self, user: User, amount: int) -> str:
        activities = (
            Activity.select()
            .where(Activity.user == user)
            .order_by(Activity.timestamp.desc())
            .limit(amount)
        )
        if len(activities) == 0:
            return "No activities found"
        lines = []
        for act in activities:
            emulated = " (emu)" if act.emulated else ""
            lines.append(
                f"#{act}\t{act.timestamp.isoformat().split(".")[0].replace("T"," ")} UTC\t{act.game.name} ({act.platform.abbreviation}){emulated}\t{utils.secsToHHMMSS(act.seconds)}"
            )
        out = "```\n"
        out += "\n".join(reversed(lines))
        out += "```"
        return out
