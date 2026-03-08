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
        # Check for a conflict with another game of the same name and the same target year.
        # This applies both when setting a specific year and when unsetting (year=null):
        # two games with the same name and null release year would break the !add_game guard.
        if year is not None:
            conflict = Game.get_or_none(  # type: ignore
                (Game.name == game.name)  # type: ignore
                & (Game.release_year == year)  # type: ignore
                & (Game.id != game.id)  # type: ignore
            )
        else:
            conflict = Game.get_or_none(  # type: ignore
                (Game.name == game.name)  # type: ignore
                & (Game.release_year.is_null())  # type: ignore
                & (Game.id != game.id)  # type: ignore
            )
        if conflict:
            year_str = str(year) if year is not None else "null"
            return (
                f"Error: A game named '{conflict.name}' with release year {year_str} "  # type: ignore
                f"already exists (id: {conflict.id})."  # type: ignore
            )
        game.release_year = year
        game.save()
        return f"{game.name} - release year set to: `{game.release_year}`"
