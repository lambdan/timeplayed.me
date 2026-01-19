from tpbackend.globals import ADMINS
from tpbackend.storage.storage_v2 import User
from abc import ABC, abstractmethod


class Command(ABC):
    names: list[str]
    description: str
    help: str

    def __init__(
        self,
        names: list[str],
        description: str,
        help="No additional help available for this command",
    ):
        self.names = names
        self.description = description
        self.help = help

    def can_execute(self, user: User, msg: str) -> bool:
        return not user.bot_commands_blocked

    def is_admin(self, user: User) -> bool:
        return str(user.id) in ADMINS

    def get_help_message(self) -> str:
        msg = "**" + self.names[0] + "** - " + self.description + "\n"
        if len(self.names) > 1:
            joined = ""
            for n in self.names[1:]:
                joined += f"{n} "
            joined = joined.strip()
            msg += f"Aliases: `{joined}`\n"
        msg += self.help
        return msg

    @abstractmethod
    def execute(self, user: User, msg: str) -> str:
        pass
