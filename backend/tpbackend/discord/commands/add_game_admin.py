from tpbackend.game.select import GameSelect
from tpbackend.storage import Game, User
from .admin_command import AdminCommand
from typing import cast


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
        return self.add(name, user)

    def add(self, s: str, user: User) -> str:
        # Block if a game with this exact name and no release year already exists.
        # (set year on the existing to disambiguate)
        existing = GameSelect.by_name_and_year(s, None)
        if existing:
            return f"Error: Game with that name and no release year already exists {existing.get_name()} (id: {existing.get_id()})"
        game = Game.create(name=s)  # type: ignore
        game = cast(Game, game)
        game.add_history(f"Game added by admin {user.get_name()}")
        game.save()

        return f"✅ Game added manually:\n- *{game.name}*\n- id: {game.id}"  # type: ignore
