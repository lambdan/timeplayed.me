from tpbackend.storage.storage_v2 import User, Platform
from tpbackend.cmds.command import Command
from tpbackend.utils import search_platforms


class ListPlatformsCommand(Command):
    def __init__(self):
        super().__init__(
            ["platforms", "search_platforms"],
            "List available platforms. Optionally provide a search query, for example: `!platforms ps`.",
        )

    def execute(self, user: User, msg: str) -> str:
        platforms = search_platforms(query=msg or "", limit=0, offset=0)
        if len(platforms) == 0:
            return "No platforms found"
        out = "```"
        for p in platforms:
            padded_id = str(p.id).rjust(3, " ")  # type: ignore
            padded_abbr = p.abbreviation.ljust(12, " ")  # type: ignore
            out += f"{padded_id}: {padded_abbr}\t{p.name if p.name else ""}\n"  # type: ignore
        out += "```"
        return out
