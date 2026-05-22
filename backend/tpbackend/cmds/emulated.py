from tpbackend.storage.storage_v2 import Activity_or_none, Platform, User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Activity


class ToggleEmulatedCommand(Command):
    def __init__(self):
        names = ["emulated", "e", "emu"]
        d = "Toggle emulated flag on activity"
        h = "Usage: `!emulated <activity_id>`"

        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        activity_id = int(msg)
        act = Activity_or_none(activity_id)
        if not act:
            return f"Error: Activity with id {activity_id} not found."
        if act.get_user() != user:
            return "Error: not your activity!"
        act.set_emulated(not act.get_emulated())
        act.save()
        return f"Activity {activity_id} emulated: {act.emulated}"
