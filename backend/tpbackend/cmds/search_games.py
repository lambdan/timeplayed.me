from tpbackend.api_v2.games.query import GameQuery
from tpbackend.storage.storage_v2 import User, Game
from tpbackend.cmds.command import Command
from tpbackend.utils import game_name
from typing import cast


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
        return self.search(msg, self.is_admin(user))

    def search(self, query: str, is_admin: bool) -> str:
        games = GameQuery.search(GameQuery.base(include_hidden=is_admin), search=query)
        if len(games) == 0:
            return "No games found"

        out = ""
        count = 0
        for game in games:
            game = cast(Game, game)
            count += 1
            out += f"- **{game.id}** - {game_name(game, as_markdown_link=True)} {"🙈" if game.get_hidden() else ""}\n"  # type: ignore
            if count >= 15 or len(out) >= 666:
                break
        msg = ""
        msg += out
        if count < len(games):
            remaining = len(games) - count
            msg += f"... and {remaining} more"
        return msg
