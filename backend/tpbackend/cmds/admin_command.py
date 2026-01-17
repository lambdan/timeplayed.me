from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
import discord


class AdminCommand(Command):
    def __init__(self, name: list[str], description: str):
        super().__init__(name, description)

    def can_execute(self, user: User, message: discord.Message) -> bool:
        if not super().can_execute(user, message):
            return False
        return self.is_admin(user)
