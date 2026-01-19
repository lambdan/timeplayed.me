from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.storage.storage_v2 import Game


class SearchGamesCommand(Command):
    def __init__(self):
        h = """
Search for games in the database.
Usage: `!search <query>`
Example: ```
!search zelda
!s mario
```
Returns: list of game id's and names matching the query
        """
        super().__init__(["search", "s", "search_game"], "Search games", help=h)

    def execute(self, user: User, msg: str) -> str:
        if msg == "":
            return "No query provided. See `!help search` for usage."
        return self.search(msg)

    def search(self, query: str) -> str:
        games = (
            Game.select()
            .where((Game.name.contains(query)) | (Game.aliases.contains(query)))
            .order_by(Game.name)
            .limit(50)
        )
        if not games:
            return "No games found"

        out = ""
        for game in games:
            out += f"- **{game.id}** - {game.name}\n"
        return out
