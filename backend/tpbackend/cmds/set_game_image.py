from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game


class SetGameImageCommand(AdminCommand):
    def __init__(self):
        names = ["set_game_image_url", "sgiu"]
        d = "Set game image by url (link to an image)"
        h = f"Usage: `!{names[0]} <game_id> <url>`. Use null as url to unset."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        url = None
        if splitted[1].strip().lower() != "null":
            url = splitted[1].strip()
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        game.image_url = url
        game.save()
        return f"{game.name} - Image set to: `{game.image_url}`"
