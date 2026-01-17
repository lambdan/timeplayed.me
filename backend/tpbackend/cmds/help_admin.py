from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.command_list import ADMIN_COMMANDS


class HelpAdminCommand(AdminCommand):
    def __init__(self):
        super().__init__(["help_admin"], "Shows admin commands")

    def execute(self, user: User, message: discord.Message) -> str:
        msg = ""
        for c in ADMIN_COMMANDS:
            msg += f"- `!{c.name}` - {c.description}\n"
        return msg
