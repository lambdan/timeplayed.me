from tpbackend.cmds.manual_activity_command import ManualActivityCommand
from tpbackend.storage.storage_v2 import LiveActivity_or_none, User, LiveActivity
import datetime
from tpbackend import utils


class TimeManualCommand(ManualActivityCommand):
    def __init__(self):
        names = ["time", "t"]
        d = "Get current duration of running manual activity (started by `!start`)"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        live = LiveActivity_or_none(user=user)
        if not live:
            return "Error: no manual activity running"

        started = live.get_started_datetime()
        duration = utils.now() - started
        seconds = int(duration.total_seconds())
        game_name = live.game.name
        return f"You have been playing *{game_name}* for {utils.secsToHHMMSS(seconds)}"
