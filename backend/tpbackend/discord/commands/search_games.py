from tpbackend.game.query import GameQuery
from tpbackend.game.select import GameSelect
from tpbackend.storage import User, Game
from .command import Command
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
        # start with _ for select debugging
        if query.startswith("_"):
            query = query[1:]
            g = GameSelect.by_name_or_alias(query)
            if g:
                return f"Found {g.get_name()} {g.get_id()}"
            else:
                return "Not found"

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
