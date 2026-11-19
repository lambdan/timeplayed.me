from tpbackend.discord.commands.admin_command import AdminCommand
from tpbackend.storage import User


class Example(AdminCommand):
    def __init__(self):
        super().__init__(names=["example"], description="Example")

    def execute(self, user: User, msg: str) -> str:
        return "ok"


class TestAdminCommand:
    def test_admins_only(self):
        command = Example()
        assert command.can_execute(User(permissions=["commands", "admin"]), "")
        assert not command.can_execute(User(permissions=["commands"]), "")

    def test_still_needs_commands(self):
        assert not Example().can_execute(User(permissions=["admin"]), "")
