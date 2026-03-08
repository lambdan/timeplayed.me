from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game


class SetSGDBIDCommand(AdminCommand):
    def __init__(self):
        names = ["set_sgdb_id", "set_sgdb", "sgdb"]
        d = "Set SGDB ID for game"
        h = f"Usage: `!{names[0]} <game_id> <sgdb_id>`. Use null for sgdb_id to clear."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        sgdb_id = None
        if splitted[1].strip().lower() != "null":
            sgdb_id = int(splitted[1].strip())
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        # any game that already has this sgdb_id?
        # (special case for 0, multiple games can have sgdb_id 0, its for games that are not in SGDB)
        # (None/null means the game is missing SGDB id, so also multiple games can have that)
        if sgdb_id != 0 and sgdb_id is not None:
            existing_game = Game.get_or_none(Game.sgdb_id == sgdb_id)  # type: ignore
            if existing_game and existing_game.id != game.id:
                return f"Error: SGDB ID {sgdb_id} is already assigned to '{existing_game.name}' (id: {existing_game.id})"  # type: ignore
        game.sgdb_id = sgdb_id
        game.save()
        return f"{game.name} - SGDB ID set to: {game.sgdb_id}"
