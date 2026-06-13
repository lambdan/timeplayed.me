import datetime
from tpbackend.storage import User
from tpbackend.utils2 import ts_to_dt
from .command import Command
from tpbackend.sgdb.controller import search


class SearchSGDBCommand(Command):
    def __init__(self):
        h = """
Search for games on SGDB
Usage: `!search_sgdb <query>`
Returns: list of SGDB id's, names and years matching the query
        """
        super().__init__(["search_sgdb", "ssgdb"], "Search SGDB", help=h)

    def execute(self, user: User, msg: str) -> str:
        if msg == "":
            return "No query provided. See `!help search_sgdb` for usage."
        return self.search(msg)

    def search(self, query: str) -> str:
        sgdb_results = search(query=query)
        if len(sgdb_results) == 0:
            return "No games found on SGDB"
        out = ""
        count = 0
        for result in sgdb_results:
            count += 1
            # convert timestamp to year
            rd = ts_to_dt(result.release_date) if result.release_date else None
            year = rd.year if rd else "?"
            out += f"- **{result.id}** - {result.name} ({year}) \n"
            # out += f"- **{result.id}** - [{result.name}](https://www.steamgriddb.com/game/{result.id}) ({year}) \n"
            if len(out) > 1337:
                out += f"... and {len(sgdb_results) - count} more"
                break
        return out.strip()
