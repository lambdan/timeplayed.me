from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.utils import search_games


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
        games = search_games(query)
        if len(games) == 0:
            return "No games found"

        out = ""
        for game in games:
            out += f"- **{game.id}** - {game.name}\n"  # type: ignore
        return out
