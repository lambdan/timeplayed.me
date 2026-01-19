from tpbackend.storage.storage_v2 import User
import discord
from tpbackend.cmds.admin_command import AdminCommand
import datetime


class UptimeCommand(AdminCommand):
    started = 0

    def __init__(self):
        super().__init__(["uptime"], "Bot uptime")
        self.started = datetime.datetime.now().timestamp()

    def execute(self, user: User, message: discord.Message) -> str:
        now = datetime.datetime.now().timestamp()
        uptime_seconds = int(now - self.started)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        return f"Bot uptime: {uptime_str}"
