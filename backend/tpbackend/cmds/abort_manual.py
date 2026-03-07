from tpbackend.storage.storage_v2 import Platform, User, LiveActivity
from tpbackend.cmds.command import Command


class AbortManualCommand(Command):
    def __init__(self):
        names = ["abort"]
        d = "Abort manual activity (started by `!start`)"
        super().__init__(names=names, description=d)

    def execute(self, user: User, msg: str) -> str:
        live = LiveActivity.get_or_none(LiveActivity.user == user)
        if not live:
            return "Error: no manual activity running"

        game_name = live.game.name
        live.delete_instance()
        return f"Aborted *{game_name}* activity"
