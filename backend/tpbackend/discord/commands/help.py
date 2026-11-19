from tpbackend.storage import User
from .command import Command
from ..command_list import COMMANDS


class HelpCommand(Command):
    def __init__(self):
        super().__init__(["help", "h"], "Shows commands")

    def execute(self, user: User, msg: str) -> str:
        if msg == "":
            return self.command_list(user=user)
        else:
            return self.individual_help(user=user, command_name=msg)

    def command_list(self, user: User) -> str:
        msg = ""
        for c in COMMANDS:
            if c.can_execute(user, ""):
                msg += f"- `!{c.names[0]}` - {c.description}\n"
        msg += "\nUse `!help <command>` for more info"
        return msg

    def individual_help(self, user: User, command_name: str) -> str:
        command_name = command_name.removeprefix("!")
        # stupid hax because of circular import hell
        if command_name == "help":
            return self.get_help_message()
        for c in COMMANDS:
            for name in c.names:
                if name == command_name:
                    if c.can_execute(user, ""):
                        return c.get_help_message()
        return f"Command `{command_name}` not found."
