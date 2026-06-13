from tpbackend.storage import User
from .command import Command


class AdminCommand(Command):
    def __init__(
        self,
        names: list[str],
        description: str,
        help="No additional help available for this command",
    ):
        super().__init__(names=names, description=description, help=help)

    def can_execute(self, user: User, msg: str) -> bool:
        return super().can_execute(user, msg) and self.is_admin(user)
