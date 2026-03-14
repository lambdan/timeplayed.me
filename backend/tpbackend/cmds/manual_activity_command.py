from tpbackend.permissions import PERMISSION_MANUAL_ACTIVITY
from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command


class ManualActivityCommand(Command):
    def __init__(
        self,
        names: list[str],
        description: str,
        help="No additional help available for this command",
    ):
        super().__init__(names=names, description=description, help=help)

    def can_execute(self, user: User, msg: str) -> bool:
        return user.has_permission(PERMISSION_MANUAL_ACTIVITY) and super().can_execute(
            user, msg
        )
