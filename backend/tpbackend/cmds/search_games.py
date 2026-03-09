from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.utils import game_name, search_games


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
        games = search_games(query=query, limit=0, offset=0)
        if len(games) == 0:
            return "No games found"

        out = ""
        count = 0
        for game in games:
            count += 1
            out += f"- **{game.id}** - {game_name(game, as_markdown_link=True)}\n"  # type: ignore
            if count >= 15 or len(out) >= 666:
                break
        msg = ""
        msg += out
        if count < len(games):
            remaining = len(games) - count
            msg += f"... and {remaining} more"
        return msg
