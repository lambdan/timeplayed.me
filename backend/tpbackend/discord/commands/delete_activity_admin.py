from tpbackend.storage import Activity_or_none, User
from .admin_command import AdminCommand


class DeleteActivityAdminCommand(AdminCommand):
    def __init__(self):
        names = ["adm_delete"]
        d = "Delete activity for any user"
        h = "Usage: `!adm_delete <activity_id>`. You can provide multiple IDs separated by commas: `!adm_delete 1,2,3`"

        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        output = ""
        ids = msg.split(",")
        for id_str in ids:
            activity_id = int(id_str.strip())
            output += f"- {activity_id}: "
            output += self.delete(activity_id)
            output += "\n"
        return output.strip()

    def delete(self, activity_id: int) -> str:
        act = Activity_or_none(activity_id)
        if not act:
            return "not found"
        act.delete_instance()
        return "deleted"
