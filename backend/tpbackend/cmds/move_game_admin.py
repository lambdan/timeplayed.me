from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.cmds.move_game import execute_move_game
from tpbackend.storage.storage_v2 import User


class MoveGameAdminCommand(AdminCommand):
    def __init__(self):
        names = ["adm_move_game", "amg"]
        d = "Move all activities of a game to another game (all users)"
        h = f"""
Move all activities (all users) from one game to another.

Usage: `!{names[0]} <from_game_id> <to_game_id> [y]`
Example: move all game 4 activities into game 35:
```
!{names[0]} 4 35
```

Returns: Confirmation message
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        return execute_move_game(msg, self.names[0], user_filter=None)
