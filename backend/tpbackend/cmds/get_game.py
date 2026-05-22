from tpbackend.storage.storage_v2 import Game_or_none, User, Game
from tpbackend.cmds.command import Command
from tpbackend.utils import game_url


class GetGameCommand(Command):
    def __init__(self):
        names = ["get_game", "gg"]
        d = "Get game info"
        h = "Get a game by ID\nUsage: `!get_game <game_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game = Game_or_none(int(msg))
        if not game:
            return f"Error: Game with id {msg} not found."

        aliases_list = []
        for alias in game.aliases:
            aliases_list.append(alias)

        msg = ""
        msg += f"## {game.get_name()}\n"
        url = game_url(game.get_id())
        if url:
            msg += f"- ID: [{game.get_id()}]({url})\n"
        else:
            msg += f"- ID: {game.get_id()}\n"
        if len(aliases_list) > 0:
            msg += "Aliases: ```"
            for alias in aliases_list:
                msg += f"{alias}\n"
            msg += "```\n"
        if game.get_sgdb_id():
            msg += f"- SGDB ID: [{game.get_sgdb_id()}](https://www.steamgriddb.com/game/{game.get_sgdb_id()})\n"
        else:
            msg += "- SGDB ID: None\n"
        msg += f"- Year: {game.get_release_year()}\n"

        if self.is_admin(user):
            msg += "# History\n```"
            for h in game.get_history():
                msg += h + "\n"
            msg += "```"

        return msg.strip()
