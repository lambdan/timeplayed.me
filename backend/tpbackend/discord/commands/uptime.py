from tpbackend.storage import User
from .admin_command import AdminCommand
import datetime


class UptimeCommand(AdminCommand):
    started = datetime.datetime.now()

    def __init__(self):
        super().__init__(["uptime"], "Bot uptime")
        self.logger.info(f"Uptime command init. Started: {self.started}")

    def execute(self, user: User, msg: str) -> str:
        now = datetime.datetime.now()
        uptime_seconds = int((now - self.started).total_seconds())
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        uptime_str = f"{days} days, {str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"
        return f"Bot uptime: {uptime_str}"
