from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.permissions import ALL_PERMISSIONS


class RemovePermissionCommand(AdminCommand):
    def __init__(self):
        names = ["remove_permission", "permission_remove", "rpe"]
        d = "Remove a permission from user"
        h = f"Usage: `!{names[0]} <user_id> <permission_name>`"
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
        if target_user.has_permission(permission_name):
            target_user.remove_permission(permission_name)
            return "OK, permission was removed"
        target_user_permissions = ",".join(target_user.permissions)
        return f"Permission NOT removed (user probably didn't have it). User has these permissions: `{target_user_permissions}`"
