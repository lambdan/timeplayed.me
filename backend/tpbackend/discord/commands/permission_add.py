from .admin_command import AdminCommand
from tpbackend.storage import User, User_or_none
from tpbackend.permissions import ALL_PERMISSIONS

VALID_PERMISSIONS_STR = ", ".join(ALL_PERMISSIONS)


class AddPermissionCommand(AdminCommand):
    def __init__(self):
        names = ["add_permission", "permission_add", "ape"]
        d = "Add a permission to user"
        h = f"Usage: `!{names[0]} <user_id> <permission_name>`. Valid permissions: `{VALID_PERMISSIONS_STR}`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) == 0:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."

        user_id = splitted[0].strip()
        if user_id == "":
            return f"Invalid syntax. See `!help {self.names[0]}` for help."

        target_user = User_or_none(user_id)
        if not target_user:
            return f"Error: User with id {user_id} not found."

        permission_name = splitted[1].strip().lower() if len(splitted) > 1 else ""
        if permission_name not in ALL_PERMISSIONS:
            return f"Error: Invalid permission. Valid permissions: `{VALID_PERMISSIONS_STR}`"
        if target_user.add_permission(permission_name):
            target_user.save()
            return "OK, permission was added"
        return "Permission NOT added (user probably had it already)"
