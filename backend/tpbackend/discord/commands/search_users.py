from tpbackend.storage import User
from .command import Command
from tpbackend.user.query import UserQuery
from tpbackend.user.utils import md_user_link


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
        results = UserQuery.search(UserQuery.base(), msg).limit(10)
        results = UserQuery.apply_sort(results, "name", "asc")
        results = list(results)
        if len(results) == 0:
            return "No users found"
        return self.print(results=results, show_permissions=self.is_admin(user))

    def print(self, results: list[User], show_permissions=False) -> str:
        out = ""
        for r in results:
            out += f"- {md_user_link(r)} ({r.get_id()})"
            if show_permissions:
                out += f" `{",".join(r.permissions)}`"
            out += "\n"
            if len(out) > 1500:
                return "Output too long. Narrow your search."
        return out
