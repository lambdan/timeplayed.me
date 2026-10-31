"""shared by the igdb and sgdb commands, matching our games with games from those services"""

from tpbackend.game.select import GameSelect
from tpbackend.storage import Game


def adopt_name(game: Game, external_name: str, source: str) -> tuple[str, bool]:
    """
    if the names differ, take the external name and keep ours as alias.
    returns (report, conflict), conflict means another game already has that name so we didn't rename
    """
    if external_name == game.get_name():
        return "", False

    out = "⚠️ Name mismatch!"
    out += f"\n- Our name: `{game.get_name()}`"
    out += f"\n- {source} name: `{external_name}`"
    if external_name in game.get_aliases():
        return out + "\n", False

    other = GameSelect.by_name_or_alias(external_name)
    if other and other.get_id() != game.get_id():
        out += f"\n OTHER GAME HAS {source} NAME AS NAME OR ALIAS: '{other.get_label()}' (id: {other.get_id()})"
        return out, True

    old_name = game.get_name()
    game.set_name(external_name)
    game.add_alias(old_name)
    out += f"\n- Replaced name with {source} name and added old name as alias\n"
    return out, False
