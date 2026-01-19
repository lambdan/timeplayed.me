from tpbackend.storage.storage_v2 import User, LiveActivity
from tpbackend.cmds.command import Command
import datetime
from tpbackend import utils, operations


class StopManualCommand(Command):
    def __init__(self):
        names = ["stop"]
        d = "Stop manual activity"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        return self.stop(user)

    def stop(self, user: User) -> str:
        # !stop
        live = LiveActivity.get_or_none(LiveActivity.user == user)
        if not live:
            return "Error: You haven't started playing anything"

        started: datetime.datetime = live.started
        if started.tzinfo is None:
            # tz info is lost in the database, assume UTC
            started = started.replace(tzinfo=datetime.timezone.utc)
        duration = utils.now() - started
        seconds = int(duration.total_seconds())

        result = operations.add_session(
            user=user, platform=live.platform, game=live.game, seconds=seconds
        )

        sesh = result[0]
        live.delete_instance()  # Remove the live session from db
        if sesh:
            msg = f"✅ Activity {sesh} saved.\n"
            msg += f"Game: *{sesh.game.name}*\n"
            msg += f"Duration: {utils.secsToHHMMSS(int(str(sesh.seconds)))}\n"
            return msg
        if isinstance(result[1], ValueError):
            return "Session ended, but not saved because it was too short"
        return "Something went wrong..."
