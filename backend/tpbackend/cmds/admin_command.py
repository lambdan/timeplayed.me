from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
import discord


class AdminCommand(Command):
    def __init__(self, name: list[str], description: str):
        super().__init__(name, description)

    def can_execute(self, user: User, message: discord.Message) -> bool:
        return super().can_execute(user, message) and self.is_admin(user)
