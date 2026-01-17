from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Activity


class DeleteActivityCommand(Command):
    def __init__(self):
        names = ["delete", "d", "del", "remove"]
        d = "Delete an activity"
        h = "Usage: `!delete <activity_id>`"

        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        activity_id = int(msg[1])
        return self.delete(user, activity_id)

    def delete(self, user: User, activity_id: int) -> str:
        act = Activity.get_or_none(Activity.id == activity_id)  # type: ignore
        if not act:
            return f"Error: Activity {activity_id} not found"
        if act.user != user:
            return "Error: not your activity!"
        act.delete_instance()
        return f"Activity {activity_id} deleted!"
