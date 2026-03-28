from tpbackend.cmds.manual_activity_command import ManualActivityCommand
from tpbackend.storage.storage_v2 import LiveActivity_or_none, User
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
        live = LiveActivity_or_none(user=user)
        if not live:
            return "Error: You haven't started playing anything"

        started = live.get_started_datetime()
        duration = utils.now() - started
        seconds = int(duration.total_seconds())

        result = operations.add_session(
            user=user,
            platform=live.get_platform(),
            game=live.get_game(),
            seconds=seconds,
        )

        sesh = result[0]
        live.delete_instance()  # Remove the live session from db
        if sesh:
            msg = f"{activity_name(sesh, as_markdown_link=True)} saved ✅\n"
            msg += f"- Game: *{game_name(sesh.get_game(), as_markdown_link=True)}*\n"  # type: ignore
            msg += f"- Duration: {utils.secsToHHMMSS(sesh.get_seconds())}\n"
            msg += f"- Platform: {sesh.get_platform().get_display_name()}\n"
            return msg.strip()
        if isinstance(result[1], ValueError):
            return "Session ended, but not saved because it was too short"
        return "Something went wrong..."
