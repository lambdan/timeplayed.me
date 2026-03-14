from tpbackend.cmds.manual_activity_command import ManualActivityCommand
from tpbackend.storage.storage_v2 import User, LiveActivity
import datetime
from tpbackend import utils, operations
from tpbackend.utils import activity_name, game_name


class StopManualCommand(ManualActivityCommand):
    def __init__(self):
        names = ["stop"]
        d = "Stop manual activity (started by `!start`) and save it"
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
            msg = f"{activity_name(sesh, as_markdown_link=True)} saved ✅\n"
            msg += f"- Game: *{game_name(sesh.game, as_markdown_link=True)}*\n"  # type: ignore
            msg += f"- Duration: {utils.secsToHHMMSS(int(str(sesh.seconds)))}\n"
            msg += f"- Platform: {sesh.platform.name or sesh.platform.abbreviation}\n"
            return msg.strip()
        if isinstance(result[1], ValueError):
            return "Session ended, but not saved because it was too short"
        return "Something went wrong..."
