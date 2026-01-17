from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.command import Command


class SearchCommand(Command):
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
        super().__init__(["search", "s"], "Search games", help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        return "TODO"
