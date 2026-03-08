import datetime
from tpbackend import steamgriddb
from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.utils import query_normalize


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
        query = query_normalize(query)
        sgdb_results = steamgriddb.search(query=query)
        if len(sgdb_results) == 0:
            return "No games found on SGDB"
        out = ""
        count = 0
        for result in sgdb_results:
            count += 1
            # convert timestamp to year
            year = (
                datetime.datetime.utcfromtimestamp(result.release_date).year
                if result.release_date
                else "?"
            )
            out += f"- **{result.id}** - {result.name} ({year}) \n"
            # out += f"- **{result.id}** - [{result.name}](https://www.steamgriddb.com/game/{result.id}) ({year}) \n"
            if len(out) > 1337:
                out += f"... and {len(sgdb_results) - count} more"
                break
        return out.strip()
