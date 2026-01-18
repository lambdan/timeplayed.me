from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.storage.storage_v2 import Game


class SetSteamIDCommand(AdminCommand):
    def __init__(self):
        names = ["set_steam_id", "set_steam", "steam"]
        d = "Set Steam ID for game"
        h = f"Usage: `!{names[0]} <game_id> <steam_id>`. Use null as steam_id to unset."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        steam_id = None
        if splitted[1].strip().lower() != "null":
            steam_id = int(splitted[1].strip())
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        game.steam_id = steam_id
        game.save()
        return f"{game.name} - Steam ID set to: {game.steam_id}"
