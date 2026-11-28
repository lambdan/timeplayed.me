from typing import Literal
from pydantic import BaseModel, Field
from tpbackend.utils2 import dt_to_ts
from tpbackend.common.models import BaseTotals
from tpbackend.files.images import public_url


class GameStats(BaseTotals):
    user_count: int
    platform_count: int


class API_Game(BaseModel):
    id: int
    name: str
    igdb_id: int | None
    igdb_url: str | None = Field(description="The game's page on IGDB")
    steam_id: int | None
    cover_disabled: bool
    nsfw: bool = Field(description="This game or a parent is NSFW")
    aliases: list[str]
    release_year: int | None
    created: int
    updated: int
    children_ids: list[int]
    parent_id: int | None
    color_primary: str | None = Field(
        description="Background for the game's tiles, hex without #. The parent's if the game "
        "has none"
    )
    color_secondary: str | None = Field(description="Text on color_primary")

    @classmethod
    def from_game(cls, game):
        color_primary, color_secondary = game.get_colors()
        return cls(
            id=game.id,
            name=game.name,
            igdb_id=game.igdb_id,
            igdb_url=game.get_igdb_url(),
            steam_id=game.steam_id,
            cover_disabled=game.get_cover_disabled(),
            nsfw=game.get_nsfw(),
            aliases=game.aliases,
            release_year=game.release_year,
            created=dt_to_ts(game.created),
            updated=dt_to_ts(game.updated),
            children_ids=[child.id for child in game.children],
            parent_id=game.parent_id,
            color_primary=color_primary,
            color_secondary=color_secondary,
        )


class API_GameWithStats(API_Game):
    stats: GameStats

    @classmethod
    def from_game(cls, game):
        color_primary, color_secondary = game.get_colors()
        return cls(
            id=game.id,
            name=game.name,
            igdb_id=game.igdb_id,
            igdb_url=game.get_igdb_url(),
            steam_id=game.steam_id,
            cover_disabled=game.get_cover_disabled(),
            nsfw=game.get_nsfw(),
            aliases=game.aliases,
            release_year=game.release_year,
            created=dt_to_ts(game.created),
            updated=dt_to_ts(game.updated),
            children_ids=[child.id for child in game.children],
            parent_id=game.parent_id,
            color_primary=color_primary,
            color_secondary=color_secondary,
            stats=GameStats(
                seconds=game.total_seconds,
                activity_count=game.activity_count,
                user_count=game.user_count,
                platform_count=game.platform_count,
                last_activity=(
                    dt_to_ts(game.last_activity) if game.last_activity else None
                ),
                first_activity=(
                    dt_to_ts(game.first_activity) if game.first_activity else None
                ),
            ),
        )


CoverVersion = Literal["original", "display", "thumbnail", "preview"]


class API_CoverImage(BaseModel):
    url: str = Field(
        description="The file, it never changes so it can be cached for good"
    )
    content_type: str
    width: int
    height: int

    @classmethod
    def from_image(cls, image):
        return cls(
            url=public_url(image),
            content_type=image.get_content_type(),
            width=image.get_width(),
            height=image.get_height(),
        )


class API_GameCover(BaseModel):
    """
    what's available of the cover. Each version is also at /game/{game_id}/cover/{version}
    """

    source: Literal["Uploaded", "IGDB", "Disabled", "None"] = Field(
        description="Disabled: turned off for this game. None: no cover found"
    )
    credits: str | None = None
    versions: dict[CoverVersion, API_CoverImage] = Field(
        default={},
        description="original: as uploaded or downloaded. display: what the game page shows. "
        "thumbnail: for small covers in lists. preview: a few pixels, to show blurred. "
        "Empty if there's no cover",
    )
