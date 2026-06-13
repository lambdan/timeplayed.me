from tpbackend.game.select import GameSelect
from tpbackend.storage import User
from .command import Command
from tpbackend.game.utils import game_url, md_game_link
from tpbackend.utils2 import js_iso


class GetGameCommand(Command):
    def __init__(self):
        names = ["get_game", "gg"]
        d = "Get game info"
        h = "Get a game by ID\nUsage: `!get_game <game_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game = GameSelect.by_id(msg)
        if not game:
            return f"Error: Game with id {msg} not found."

        aliases_list = []
        for alias in game.aliases:
            aliases_list.append(alias)

        msg = ""
        msg += f"{md_game_link(game)}\n"

        parent = game.get_parent()
        if parent:
            msg += f"### Child of {parent.get_name()} ({parent.get_id()})\n"

        if game.get_sgdb_id():
            msg += f"- SGDB ID: [{game.get_sgdb_id()}](https://www.steamgriddb.com/game/{game.get_sgdb_id()})\n"
        else:
            msg += "- SGDB ID: None\n"
        msg += f"- Year: {game.get_release_year()}\n"
        msg += f"- Created: {js_iso(game.get_created())}\n"
        msg += f"- Updated: {js_iso(game.get_updated())}\n"

        if len(aliases_list) > 0:
            msg += "Aliases:\n```"
            for alias in aliases_list:
                msg += f"{alias}\n"
            msg += "```\n"

        if self.is_admin(user):
            msg += "# History\n"
            if len(game.get_history()) == 0:
                msg += "No history\n"
            else:
                msg += "```"
                for h in game.get_history():
                    msg += h + "\n"
                msg += "```"

        return msg.strip()
