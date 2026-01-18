from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.operations import get_game_by_name_or_alias
from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.storage.storage_v2 import Game


class AddGameAliasCommand(AdminCommand):
    def __init__(self):
        names = ["add_game_alias", "aga"]
        d = "Add game alias"
        h = f"Usage: `!{names[0]} <game_id> <new_alias>`. Aliases are case sensitive!!"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) < 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = int(splitted[0].strip())
        game = Game.get_or_none(Game.id == game_id)  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        new_alias = " ".join(splitted[1:]).strip()
        game_by_alias = get_game_by_name_or_alias(new_alias)
        if game_by_alias:
            return f"Error: Alias is already in use by '{game_by_alias.name}' (id: {game_by_alias.id})"  # type: ignore
        game.aliases.append(new_alias)
        game.save()
        return f"Added alias for *{game.name}*"
