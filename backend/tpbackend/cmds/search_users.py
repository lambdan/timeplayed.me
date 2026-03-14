from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command
from tpbackend.utils import search_users, user_name


class SearchUsersCommand(Command):
    def __init__(self):
        h = """
Search for users 
Usage: `!search <query>`
        """
        super().__init__(
            [
                "search_users",
                "su",
            ],
            "Search users",
            help=h,
        )

    def execute(self, user: User, msg: str) -> str:
        results = search_users(msg, limit=50)
        if len(results) == 0:
            return "No users found"
        if self.is_admin(user):
            return self.print_admin(results)
        return self.print_regular(results)

    def print_regular(self, results: list[User]) -> str:
        out = ""
        for r in results:
            out += f"- {r.id} - {user_name(r, as_markdown_link=True)}\n"
            if len(out) > 1500:
                return "Output too long. Narrow your search."
        return out

    def print_admin(self, results: list[User]) -> str:
        out = ""
        for r in results:
            out += f"### {r.id} - {user_name(r, as_markdown_link=True)}\n"
            out += f"Permissions: `{",".join(r.permissions)}`\n"
            if len(out) > 1500:
                return "Output too long. Narrow your search."
        return out
