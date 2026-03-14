from tpbackend.storage.storage_v2 import User
from tpbackend.permissions import PERMISSION_COMMANDS, PERMISSION_ADMIN
from abc import ABC, abstractmethod
import logging


class Command(ABC):
    names: list[str]
    description: str
    help: str
    logger: logging.Logger

    def __init__(
        self,
        names: list[str],
        description: str,
        help="No additional help available for this command",
    ):
        self.names = names
        self.description = description
        self.help = help
        self.logger = logging.getLogger(f"command.{self.names[0]}")

    def can_execute(self, user: User, msg: str) -> bool:
        return user.has_permission(PERMISSION_COMMANDS)

    def is_admin(self, user: User) -> bool:
        return user.has_permission(PERMISSION_ADMIN)

    def get_help_message(self) -> str:
        msg = "# " + self.names[0] + "\n"
        msg += self.description + "\n"
        if len(self.names) > 1:
            joined = ""
            for n in self.names[1:]:
                joined += f"{n} "
            joined = joined.strip()
            msg += f"Aliases: `{joined}`\n"
        msg += "-----------------\n"
        msg += self.help
        return msg

    @abstractmethod
    def execute(self, user: User, msg: str) -> str:
        pass
