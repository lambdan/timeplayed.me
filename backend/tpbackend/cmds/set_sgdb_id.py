from tpbackend import steamgriddb
from tpbackend.cmds.admin_command import AdminCommand
from tpbackend.operations import get_game_by_name_or_alias
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

        if sgdb_id == 0 or sgdb_id is None:
            game.sgdb_id = sgdb_id
            game.save()
            return f"{game.name} - SGDB ID set to: {game.sgdb_id}"

        # get info from sgdb
        sgdb_game = steamgriddb.get_game_by_id(sgdb_id)
        if not sgdb_game:
            return f"Error: No game found in SGDB with id {sgdb_id}."
        if not sgdb_game.name:
            return f"Error: SGDB game with id {sgdb_id} has no name."

        out = ""
        # check name mismatch
        if sgdb_game.name != game.name:
            out += "⚠️ Name mismatch!"
            out += f"\n- Our name: `{game.name}`"
            out += f"\n- SGDB name: `{sgdb_game.name}`"
            # maybe we can add SGDB name as an alias?
            if sgdb_game.name not in game.aliases:
                # check if any other game has that name or alias
                aliased_game = get_game_by_name_or_alias(sgdb_game.name)
                if aliased_game and aliased_game.id != game.id:  # type: ignore
                    out += f"\n OTHER GAME HAS SGDB NAME AS NAME OR ALIAS: '{aliased_game.name}' (id: {aliased_game.id})"  # type: ignore
                    out += "\n - ABORTING!"
                    return out
                old_name = game.name
                game.name = sgdb_game.name
                game.aliases.append(old_name)
                out += "\n- Replaced name with SGDB name and added old name as alias"
            out += "\n"

        # check year mismatch
        if (
            sgdb_game.release_date
            and game.release_year
            and sgdb_game.release_date.year != game.release_year
        ):
            out += "⚠️ Year mismatch!"
            out += f"\n- Our year: `{game.release_year}`"
            out += f"\n- SGDB year: `{sgdb_game.release_date.year}`"
            out += "\n"

        if game.release_year is None and sgdb_game.release_date is not None:
            game.release_year = sgdb_game.release_date.year
            out += "🗓️ Updating release year based on SGDB data\n"

        game.sgdb_id = sgdb_id
        game.save()
        out += f"OK, SGDB ID updated for *{game.name}*"
        return out
