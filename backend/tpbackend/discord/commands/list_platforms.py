from typing import cast
from tpbackend.platform.query import PlatformQuery
from tpbackend.storage import Platform, User
from .command import Command


class ListPlatformsCommand(Command):
    def __init__(self):
        super().__init__(
            ["platforms", "search_platforms"],
            "List available platforms. Optionally provide a search query, for example: `!platforms ps`.",
        )

    def execute(self, user: User, msg: str) -> str:
        q = PlatformQuery.base()
        q = PlatformQuery.search(q, search=msg.strip())
        q = PlatformQuery.apply_sort(q, sort="name", order="asc")
        platforms = q.execute()
        if len(platforms) == 0:
            return "No platforms found"
        out = ""
        for p in platforms:
            p = cast(Platform, p)
            out += f"- {p.get_display_name()} ({p.get_id()})\n"
        out += ""
        return out
