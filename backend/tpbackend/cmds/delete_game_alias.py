from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.operations import get_game_by_alias
from tpbackend.storage.storage_v2 import User


class DeleteGameAliasCommand(AdminCommand):
    def __init__(self):
        names = ["delete_game_alias", "dga", "remove_game_alias", "rga"]
        d = "Delete game alias"
        h = f"Usage: `!{names[0]} <alias>`. Aliases are case sensitive!!"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        alias = msg
        game = get_game_by_alias(alias)
        if not game:
            return "Error: No game found with that alias"
        game.aliases.remove(alias)  # type: ignore
        game.save()
        return f"Removed alias from *{game.name}*"
