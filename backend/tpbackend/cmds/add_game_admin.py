from tpbackend.storage.storage_v2 import Game, User
from tpbackend.cmds.admin_command import AdminCommand


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
        # Block if a game with this exact name and no release year already exists.
        # (A null release_year means it was manually added and not yet disambiguated.)
        # Games with the same name but a release year set are allowed — those are
        # versioned entries (e.g. RE4 2005 vs RE4 2023) managed via !add_sgdb.
        existing = Game.get_or_none(  # type: ignore
            (Game.name == s) & (Game.release_year.is_null())  # type: ignore
        )
        if existing:
            return f"Error: Game seems to already exist: '{existing.name}' (id: {existing.id})"  # type: ignore
        # Use Game.create() directly so we always produce a new row and never
        # silently return an existing game matched by alias or case-insensitive name.
        game = Game.create(name=s)  # type: ignore
        return f"✅ Game added manually:\n- *{game.name}*\n- id: {game.id}"  # type: ignore
