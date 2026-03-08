from tpbackend.storage.storage_v2 import Game, User
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.operations import get_game_by_name_or_alias_or_create


class AddGameAdminCommand(AdminCommand):
    def __init__(self):
        names = ["add_game", "ag"]
        d = "Add game to the database manually"
        h = """
Usage: `!add_game <game_name>`
Example: ```
!add_game The Legend of Zelda: Breath of the Wild
```
Returns: Confirmation message with the game ID and name.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        name = msg.strip()
        if name == "":
            return f"No game name provided? Try `!help {self.names[0]}` for help"
        return self.add(name)

    def add(self, s: str) -> str:
        # Only block true duplicates: same name with no release year.
        # Games with a release year may share names (e.g. 2005 vs 2023 versions).
        existing = Game.get_or_none(  # type: ignore
            (Game.name == s) & (Game.release_year.is_null())  # type: ignore
        )
        if existing:
            return f"Error: Game seems to already exist: '{existing.name}' (id: {existing.id})"  # type: ignore
        game = get_game_by_name_or_alias_or_create(s)
        return f"✅ Game added manually:\n- *{game.name}*\n- id: {game.id}"  # type: ignore
