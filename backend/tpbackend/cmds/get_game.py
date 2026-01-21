from tpbackend.storage.storage_v2 import User, Game
from tpbackend.cmds.command import Command


class GetGameCommand(Command):
    def __init__(self):
        names = ["get_game", "gg"]
        d = "Get game info"
        h = "Get a game by ID\nUsage: `!get_game <game_id>`"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game = Game.get_or_none(Game.id == int(msg))  # type: ignore
        if not game:
            return f"Error: Game with id {msg} not found."

        aliases_list = []
        for alias in game.aliases:
            aliases_list.append(alias)

        msg = ""
        msg += f"## {game.name}\n"
        msg += f"- ID: {game.id}\n"
        if len(aliases_list) > 0:
            msg += "Aliases: ```"
            for alias in aliases_list:
                msg += f"{alias}\n"
            msg += "```\n"

        return msg.strip()
