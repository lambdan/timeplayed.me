from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.command_list import ADMIN_COMMANDS


class HelpAdminCommand(AdminCommand):
    def __init__(self):
        super().__init__(["help_admin", "ha"], "Shows admin commands")

    def execute(self, user: User, msg: str) -> str:
        msg = ""
        for c in ADMIN_COMMANDS:
            msg += f"- `!{c.names[0]}` - {c.description}\n"
        return msg
