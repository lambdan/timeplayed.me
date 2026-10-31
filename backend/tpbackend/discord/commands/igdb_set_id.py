from tpbackend.game.select import GameSelect
from tpbackend.igdb.controller import get_game_info
from tpbackend.utils2 import ts_to_dt
from .admin_command import AdminCommand
from tpbackend.storage import User
from tpbackend.storage import Game
from .merge_game_admin import merge_and_report, merge_preview


class SetIGDBIDCommand(AdminCommand):
    def __init__(self):
        names = ["set_igdb_id", "set_igdb", "igdb"]
        d = "Set IGDB ID for game"
        h = """
Usage: `!igdb <game_id> <igdb_id|null>`

If another game already has that IGDB ID, this game gets merged into it: all its activities are moved over, its name is kept as an alias, and it's deleted (you'll be asked to confirm first).
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        splitted = msg.split(" ")
        if len(splitted) not in (2, 3):
            return f"Invalid syntax. See `!help {self.names[0]}` for help."
        confirmed = len(splitted) == 3 and splitted[2].strip().lower() == "y"
        game_id = splitted[0].strip()
        igdb_id = None
        if splitted[1].strip().lower() != "null":
            igdb_id = int(splitted[1].strip())
        game = GameSelect.by_id(game_id)
        if not game:
            return f"Error: Game with id {game_id} not found."

        if igdb_id == 0 or igdb_id is None:
            game.set_igdb_id(igdb_id)
            game.save()
            return f"{game.get_label()} - IGDB ID set to: {game.igdb_id}"

        # another game already has this igdb_id: it's the same game, merge into that one
        existing_game = Game.get_or_none(Game.igdb_id == igdb_id)
        if existing_game and existing_game.id != game.id:
            if not confirmed:
                return f"IGDB ID {igdb_id} already belongs to *{existing_game.get_label()}*.\n" + merge_preview(game, existing_game)  # type: ignore
            return merge_and_report(game, existing_game)  # type: ignore

        # get info from igdb
        igdb_game = get_game_info(igdb_id)
        if not igdb_game:
            return f"Error: No game found in IGDB with id {igdb_id}."
        if not igdb_game.name:
            return f"Error: IGDB game with id {igdb_id} has no name."

        out = ""
        # check name mismatch
        if igdb_game.name != game.name:
            out += "⚠️ Name mismatch!"
            out += f"\n- Our name: `{game.name}`"
            out += f"\n- IGDB name: `{igdb_game.name}`"
            # maybe we can add IGDB name as an alias?
            if igdb_game.name not in game.aliases:
                # check if any other game has that name or alias
                aliased_game = GameSelect.by_name_or_alias(igdb_game.name)
                if aliased_game and aliased_game.id != game.id:  # type: ignore
                    out += f"\n OTHER GAME HAS IGDB NAME AS NAME OR ALIAS: '{aliased_game.get_label()}' (id: {aliased_game.id})"  # type: ignore
                    out += "\n - NOT UPDATING NAME!"
                else:
                    old_name = game.get_name()
                    game.set_name(igdb_game.name)
                    game.add_alias(old_name)
                    out += (
                        "\n- Replaced name with IGDB name and added old name as alias"
                    )
            out += "\n"

        if igdb_game.first_release_date:
            dt = ts_to_dt(igdb_game.first_release_date)
            if dt.year != game.get_release_year():
                game.set_release_year(dt.year)
                out += f"- Release year set to {dt.year}\n"

        game.set_igdb_id(igdb_id)
        game.save()
        out += f"OK, IGDB ID updated for *{game.get_label()}*"
        return out
