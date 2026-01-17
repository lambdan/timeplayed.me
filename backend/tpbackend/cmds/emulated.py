from tpbackend.storage.storage_v2 import Platform, User
import discord
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Activity


class ToggleEmulatedCommand(Command):
    def __init__(self):
        names = ["emulated", "e", "emu"]
        d = "Toggle emulated flag on activity"
        h = "Usage: `!emulated <activity_id>`"

        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        activity_id = int(msg[1])
        act = Activity.get_or_none(Activity.id == activity_id)  # type: ignore
        if not act:
            return f"Error: Activity with id {activity_id} not found."
        if act.user != user:
            return "Error: not your activity!"
        act.emulated = not act.emulated
        act.save()
        return f"Activity {activity_id} emulated: {act.emulated}"
