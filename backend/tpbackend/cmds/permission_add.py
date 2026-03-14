from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.permissions import ALL_PERMISSIONS


class AddPermissionCommand(AdminCommand):
    def __init__(self):
        names = ["add_permission", "permission_add", "ape"]
        d = "Add a permission to user"
        h = f"Usage: `!{names[0]} <user_id> <permission_name>`. Valid permissions: `{", ".join(ALL_PERMISSIONS)}`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) == 0:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."

        user_id = splitted[0].strip()
        if user_id == "":
            return f"Invalid syntax. See `!help {self.names[0]}` for help."

        target_user = User.get_or_none(User.id == user_id)  # type: ignore
        if not target_user:
            return f"Error: User with id {user_id} not found."
        assert isinstance(target_user, User)

        permission_name = splitted[1].strip().lower() if len(splitted) > 1 else ""
        if permission_name not in ALL_PERMISSIONS:
            return f"Error: Invalid permission. Valid permissions: `{", ".join(ALL_PERMISSIONS)}`"
        if target_user.add_permission(permission_name):
            return "OK, permission was added"
        return "Permission NOT added (user probably had it already)"
