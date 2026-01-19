from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User


class BlockCommandsCommand(AdminCommand):
    def __init__(self):
        names = ["block_commands"]
        d = "Block user from commands"
        h = f"Usage: `!{names[0]} <user_id> on/off`. Send without argument to see status."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) == 0:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        user_id = splitted[0].strip()
        if user_id == "":
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        target_user = User.get_or_none(User.id == user_id)  # type: ignore
        if not target_user:
            return f"Error: User with id {user_id} not found."
        assert isinstance(target_user, User)
        if len(splitted) == 1:
            return self.status(target_user)
        status = splitted[1].strip().lower()
        if status not in ["on", "off"]:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        target_user.bot_commands_blocked = status == "on"  # type: ignore
        target_user.save()
        return self.status(target_user)

    def status(self, user: User) -> str:
        return f"{user.name} blocked from commands: {user.bot_commands_blocked}"
