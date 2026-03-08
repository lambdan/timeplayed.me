from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Activity
from tpbackend import utils

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
        return (
            Activity.select()
            .where(Activity.user == user)
            .order_by(Activity.timestamp.desc())
            .limit(amount)
        )

    def output(self, activities) -> str:
        lines = []
        for act in activities:
            emulated = " (emu)" if act.emulated else ""
            lines.append(
                f"#{act}\t{act.timestamp.isoformat().split(".")[0].replace("T"," ")} UTC\t{act.game.name} ({act.platform.abbreviation}){emulated}\t{utils.secsToHHMMSS(act.seconds)}"
            )
        out = "```\n"
        out += "\n".join(lines)
        out += "```"
        if len(out) >= 2000:
            return TOO_LONG_ERR
        return out

    def new_output(self, activities) -> str:
        out = ""
        for act in activities:
            ts = act.timestamp.isoformat().split(".")[0].replace("T", " ")
            url = utils.activity_url(act.id)
            if url:
                out += f"[#{act.id}]({url})\n"
            else:
                out += f"{act.id}\n"
            out += f"- *{utils.game_name(act.game)}*\n"
            out += f"- {act.platform.name or act.platform.abbreviation}"
            if act.emulated:
                out += " (emu)"
            out += "\n"
            out += f"- {ts} UTC\n"
            out += f"- {utils.secsToHHMMSS(act.seconds)}\n"
            out += "\n"
            if len(out) >= 2000:
                return TOO_LONG_ERR
        return out.strip()
