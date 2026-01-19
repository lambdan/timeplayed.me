from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.admin_command import AdminCommand


class SearchUsersCommand(AdminCommand):
    def __init__(self):
        h = """
Search for users in the database.
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

    def execute(self, user: User, message: discord.Message) -> str:
        # remove first
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        if msg == "":
            return "No query provided. See `!help search` for usage."
        return self.search(msg)

    def search(self, query: str) -> str:
        users = (
            User.select().where(User.name.contains(query)).order_by(User.name).limit(50)
        )
        if not users:
            return "No users found"

        out = ""
        for user in users:
            out += f"- **{user.id}** - {user.name}\n"
        return out
