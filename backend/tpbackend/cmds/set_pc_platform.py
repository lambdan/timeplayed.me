from tpbackend.storage.storage_v2 import User
from tpbackend.cmds.command import Command

VALID = ["win", "mac", "linux"]


class SetPCPlatformCommand(Command):
    def __init__(self):
        names = ["set_pc_platform", "set_pcp", "pcplatform", "pcp"]
        d = "Set PC platform"
        h = f"""
Set which PC platform your PC activities should count towards.

Valid options are: `{', '.join(VALID)}`

Check your current PC platform```
!pcplatform
```

Set your PC platform to mac```
!pcp mac
```
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        if msg == "":
            return self.get_current(user)

        new_os = msg.lower()
        return self.update(user, new_os)

    def get_current(self, user: User) -> str:
        return f"Your current PC platform is **{user.pc_platform}**."  # type: ignore

    def update(self, user: User, new_os: str) -> str:
        if new_os not in VALID:
            return f"Invalid. See `!help {self.names[0]}` for help"

        user.pc_platform = new_os  # type: ignore
        user.save()
        return f"Your PC platform is now **{user.pc_platform}**"
