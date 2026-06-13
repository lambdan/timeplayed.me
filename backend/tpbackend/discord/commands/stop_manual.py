from tpbackend.activity.utils import md_activity_link
from tpbackend.game.utils import md_game_link
from .manual_activity_command import ManualActivityCommand
from tpbackend.operations import add_session
from tpbackend.storage import LiveActivity_or_none, User
from tpbackend.utils2 import now, secsToHHMMSS


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
        duration = now() - started
        seconds = int(duration.total_seconds())

        result = add_session(
            user=user,
            platform=live.get_platform(),
            game=live.get_game(),
            seconds=seconds,
        )

        sesh = result[0]
        live.delete_instance()  # Remove the live session from db
        if sesh:
            msg = f"{md_activity_link(sesh)} saved ✅\n"
            msg += f"- {md_game_link(sesh.get_game())}\n"
            msg += f"- Duration: {secsToHHMMSS(sesh.get_seconds())}\n"
            msg += f"- Platform: {sesh.get_platform().get_display_name()}\n"

            sesh.add_history("Activity source: live activity")
            sesh.save()

            return msg.strip()
        if isinstance(result[1], ValueError):
            return "Session ended, but not saved because it was too short"
        return "Something went wrong..."
