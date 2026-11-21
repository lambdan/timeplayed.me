"""
A game's cover: uploaded by an admin, or IGDB's. Kept as an ImageFile and served from
/api/files as its smaller versions (see tpbackend/files/images.py). GameCover says which
image it is, so IGDB is only asked the first time
"""

from pathlib import PurePosixPath
from typing import Literal, cast

from peewee import IntegrityError

from tpbackend.files.images import VERSIONS, get_image, get_versions
from tpbackend.igdb import controller as igdb
from tpbackend.keyed_lock import KeyedLock
from tpbackend.storage import Game, GameCover, ImageFile

IGDB_COVER_SIZE = "t_cover_big"
fetching = KeyedLock()


class FoundCover:
    """
    where the cover is from, and its versions by name (all of them, or none for
    Disabled/None)
    """

    def __init__(
        self,
        source: Literal["Uploaded", "IGDB", "Disabled", "None"],
        versions: dict[str, ImageFile] | None = None,
        credits: str | None = None,
    ):
        self.source = source
        self.versions = versions or {}
        self.credits = credits


ORIGINAL = "original"


def all_versions(image: ImageFile) -> dict[str, ImageFile] | None:
    """
    the smaller versions, and the image as it was uploaded/downloaded as "original".
    None if the image is gone (and can't be made again)
    """
    versions = get_versions(image)
    if any(name not in versions for name in VERSIONS):
        return None
    return {ORIGINAL: image, **versions}


def cover_row(game: Game) -> GameCover | None:
    return game.get_cover()


def fetch_igdb_cover(igdb_id: int) -> tuple[ImageFile, str] | None:
    """asks IGDB which cover it is and stores it (slow). The image and the IGDB page"""
    info = igdb.get_cover_info(igdb_id)
    if not info or not info.cover:
        return None
    url = f"https://images.igdb.com/igdb/image/upload/{IGDB_COVER_SIZE}/{info.cover.image_id}.jpg"
    image = get_image(url)
    if not image:
        return None
    return image, info.url


def save_igdb_cover(game: Game, igdb_id: int, image: ImageFile, igdb_url: str):
    """
    replaces the game's IGDB cover. An uploaded one is never replaced, it comes first.
    IGDB told us the game's page too, kept on the game (if it's still that IGDB ID)
    """
    Game.update(igdb_url=igdb_url).where(
        (Game.id == game.get_id()) & (Game.igdb_id == igdb_id)
    ).execute()
    GameCover.delete().where(
        (GameCover.game == game.get_id()) & (GameCover.source == GameCover.IGDB)
    ).execute()
    try:
        GameCover.create(
            game=game.get_id(),
            image=image,
            source=GameCover.IGDB,
            igdb_id=igdb_id,
        )
    except IntegrityError:
        # saved at the same time somewhere else, or the game has an uploaded cover
        pass


def stored_igdb_image(row: GameCover | None, igdb_id: int) -> ImageFile | None:
    """the stored one, if it's the cover of the game's current IGDB ID"""
    if row and row.get_source() == GameCover.IGDB and row.get_igdb_id() == igdb_id:
        return row.get_image()
    return None


def igdb_cover(game: Game, igdb_id: int, row: GameCover | None) -> FoundCover | None:
    image = stored_igdb_image(row, igdb_id)
    if not image:
        # a page asks for several versions of a cover at once, only one asks IGDB
        with fetching.hold(str(game.get_id())):
            # it may have been stored while we waited
            image = stored_igdb_image(cover_row(game), igdb_id)
            if not image:
                fetched = fetch_igdb_cover(igdb_id)
                if not fetched:
                    return None
                image, igdb_url = fetched
                save_igdb_cover(game, igdb_id, image, igdb_url)

    versions = all_versions(image)
    if not versions:
        return None
    # IGDB's image id is the file name of the cover
    image_id = PurePosixPath(image.get_source() or "").stem
    return FoundCover("IGDB", versions, credits=f"IGDB cover image ID: {image_id}")


def find_cover(game: Game) -> FoundCover:
    """
    the uploaded cover, else IGDB's, else the parent's cover.
    only the game's own, the parent's are tried when we get to the parent.
    IGDB ID 0 means "not on IGDB", so it's skipped like no id
    """
    if game.get_cover_disabled():
        return FoundCover("Disabled")

    row = cover_row(game)
    if row and row.get_source() == GameCover.UPLOAD:
        versions = all_versions(row.get_image())
        if versions:
            return FoundCover("Uploaded", versions)

    igdb_id = cast(int | None, game.igdb_id)
    if igdb_id:
        cover = igdb_cover(game, igdb_id, row)
        if cover:
            return cover

    parent = game.get_parent()
    if parent:
        return find_cover(parent)

    return FoundCover("None")
