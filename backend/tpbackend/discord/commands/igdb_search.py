from tpbackend.igdb.controller import search_game
from tpbackend.storage import User
from tpbackend.utils2 import ts_to_dt
from .command import Command


class SearchIGDBCommand(Command):
    def __init__(self):
        h = """
Search for games on IGDB 
Usage: `!search_gdb <query>`
Returns: list of IGDB id's, names and years matching the query
        """
        super().__init__(["search_igdb", "sigdb"], "Search IGDB", help=h)

    def execute(self, user: User, msg: str) -> str:
        if msg == "":
            return "No query provided. See `!help search_igdb` for usage."
        return self.search(msg)

    def search(self, query: str) -> str:
        igdb_results = search_game(query=query)
        if len(igdb_results) == 0:
            return "No games found on IGDB"
        msg = ""
        for result in igdb_results:
            rd_ts = result.first_release_date
            rd = ts_to_dt(rd_ts) if rd_ts else None
            year = rd.year if rd else "?"
            msg += f"- **{result.id}** - [{result.name}]({result.url}) ({year})\n"
        return msg.strip()
