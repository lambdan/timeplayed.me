from tpbackend.storage.storage_v2 import User
import discord
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

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        amount = 1
        if len(msg) > 1:
            requested = int(msg[1])
            amount = max(1, min(requested, 10))
        return self.get_activities(user, amount)

    def get_activities(self, user: User, amount: int) -> str:
        activities = (
            Activity.select()
            .where(Activity.user == user)
            .order_by(Activity.timestamp.desc())
            .limit(amount)
        )
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
