from tpbackend import api
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import Platform, User
import discord
from tpbackend.storage.storage_v2 import Game


class DeletePlatformCommand(AdminCommand):
    def __init__(self):
        names = ["delete_platform", "del_platform", "remove_platform"]
        d = "Delete platform"
        h = f"Usage: `!{names[0]} <platform_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, message: discord.Message) -> str:
        msg = message.content.strip()
        msg = msg.split(" ")
        msg = " ".join(msg[1:]).strip()
        splitted = msg.split(" ")
        if len(splitted) != 1:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        platform_id = int(splitted[0].strip())
        platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
        if not platform:
            return f"Error: Platform with id {platform_id} not found."
        activities = api.get_activities(platform=platform_id)
        if activities.total > 0:
            return f"Error: platform ({platform.abbreviation}) has activities"
        platform.delete_instance()
        return f"Platform {platform_id} deleted"
