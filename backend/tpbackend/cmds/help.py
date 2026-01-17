from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.command import Command
from tpbackend.command_list import REGULAR_COMMANDS, ADMIN_COMMANDS
from tpbackend.cmds.help_admin import HelpAdminCommand


class HelpCommand(Command):
    def __init__(self):
        super().__init__(["help"], "Shows commands")

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip().lower()
        if msg == "!help":
            return self.command_list(user=user)
        else:
            command_name = msg.removeprefix("!help ").split(" ")[0]
            return self.individual_help(user=user, command_name=command_name)

    def command_list(self, user: User) -> str:
        msg = ""
        for c in REGULAR_COMMANDS:
            msg += f"- `!{c.names[0]}` - {c.description}\n"
        if self.is_admin(user):
            msg += "\n\n☣️ You are admin, see !help_admin"
        msg += "\nUse `!help <command>` for more info"
        return msg

    def individual_help(self, user: User, command_name: str) -> str:
        command_name = command_name.removeprefix("!")
        # stupid hax because of circular import hell
        if command_name == "help":
            return self.get_help_message()
        if command_name == "help_admin" and self.is_admin(user):
            return HelpAdminCommand().get_help_message()
        for c in REGULAR_COMMANDS:
            for name in c.names:
                if name == command_name:
                    return c.get_help_message()
        if self.is_admin(user):
            for c in ADMIN_COMMANDS:
                for name in c.names:
                    if name == command_name:
                        return c.get_help_message()
        return f"Command `{command_name}` not found."
