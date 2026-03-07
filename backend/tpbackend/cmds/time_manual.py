from tpbackend.storage.storage_v2 import Platform, User, LiveActivity
from tpbackend.cmds.command import Command
import datetime
from tpbackend import utils


class TimeManualCommand(Command):
    def __init__(self):
        names = ["time", "t"]
        d = "Get current duration of running manual activity (started by `!start`)"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        live = LiveActivity.get_or_none(LiveActivity.user == user)
        if not live:
            return "Error: no manual activity running"

        started: datetime.datetime = live.started
        if started.tzinfo is None:
            # tz info is lost in the database, assume UTC
            started = started.replace(tzinfo=datetime.timezone.utc)
        duration = utils.now() - started
        seconds = int(duration.total_seconds())
        game_name = live.game.name
        return f"You have been playing *{game_name}* for {utils.secsToHHMMSS(seconds)}"
