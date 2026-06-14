from tpbackend.storage import Activity_or_none, User
from .command import Command


class DeleteActivityCommand(Command):
    def __init__(self):
        names = ["delete", "d", "del", "remove"]
        d = "Delete activity"
        h = "Usage: `!delete <activity_id>`. You can provide multiple IDs separated by commas: `!delete 1,2,3`"

        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        output = ""
        ids = msg.split(",")
        for id_str in ids:
            activity_id = int(id_str.strip())
            output += f"- {activity_id}: "
            output += self.delete(user, activity_id)
            output += "\n"
        return output.strip()

    def delete(self, user: User, activity_id: int) -> str:
        act = Activity_or_none(activity_id)
        if not act:
            return "not found"
        if act.user != user:
            return "✋ Not your activity!"
        act.delete_instance()
        return "deleted"
