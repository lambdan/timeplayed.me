from tpbackend.api_v2.games.select import GameSelect
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Game_or_none, User


class AddGameAliasCommand(AdminCommand):
    def __init__(self):
        names = ["add_game_alias", "aga"]
        d = "Add game alias"
        h = f"Usage: `!{names[0]} <game_id> <new_alias>`. Aliases are case sensitive!!"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) < 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = int(splitted[0].strip())
        game = Game_or_none(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."
        new_alias = " ".join(splitted[1:]).strip()
        game_by_alias = GameSelect.by_name_or_alias(new_alias)
        if game_by_alias:
            return f"Error: Alias is already in use by '{game_by_alias.name}' (id: {game_by_alias.id})"  # type: ignore
        if game.add_alias(new_alias):
            game.save()
            return f"✅ Added alias for *{game.name}*"
        return "Failed to add alias... most likely the game already has it?"
