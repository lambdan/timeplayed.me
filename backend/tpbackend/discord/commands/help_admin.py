from tpbackend.storage import User
from .admin_command import AdminCommand
from ..command_list import ADMIN_COMMANDS


class HelpAdminCommand(AdminCommand):
    def __init__(self):
        super().__init__(["help_admin", "ha"], "Shows admin commands")

    def execute(self, user: User, msg: str) -> str:
        msg = "☣️\n"
        for c in ADMIN_COMMANDS:
            msg += f"- `!{c.names[0]}` - {c.description}\n"
        return msg
