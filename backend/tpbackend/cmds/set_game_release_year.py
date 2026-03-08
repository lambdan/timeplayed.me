from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.storage.storage_v2 import User
from tpbackend.storage.storage_v2 import Game


class SetGameReleaseYearCommand(AdminCommand):
    def __init__(self):
        names = ["set_game_release_year", "sgry"]
        d = "Set game release year"
        h = f"Usage: `!{names[0]} <game_id> <year>`. Use null as year to unset."
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) != 2:
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        game_id = splitted[0].strip()
        year = None
        if splitted[1].strip().lower() != "null":
            year = int(splitted[1].strip())
        game = Game.get_or_none(Game.id == int(game_id))  # type: ignore
        if not game:
            return f"Error: Game with id {game_id} not found."
        if year is not None:
            # Check for a different game that already has this name + year combination.
            conflict = Game.get_or_none(  # type: ignore
                (Game.name == game.name)  # type: ignore
                & (Game.release_year == year)  # type: ignore
                & (Game.id != game.id)  # type: ignore
            )
            if conflict:
                return (
                    f"Error: A game named '{conflict.name}' with release year {year} "  # type: ignore
                    f"already exists (id: {conflict.id})."  # type: ignore
                )
        game.release_year = year
        game.save()
        return f"{game.name} - release year set to: `{game.release_year}`"
