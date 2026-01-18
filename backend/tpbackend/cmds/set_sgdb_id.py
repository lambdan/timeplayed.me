from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.storage.storage_v2 import Game


class SetSGDBIDCommand(AdminCommand):
    def __init__(self):
        names = ["set_sgdb_id", "set_sgdb", "sgdb"]
        d = "Set SGDB ID for game"
        h = f"Usage: `!{names[0]} <game_id> <sgdb_id>`. Use null for sgdb_id to clear."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        sgdb_id = None
        if splitted[1].strip().lower() != "null":
            sgdb_id = int(splitted[1].strip())
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        game.sgdb_id = sgdb_id
        game.save()
        return f"{game.name} - SGDB ID set to: {game.sgdb_id}"
