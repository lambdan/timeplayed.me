from pydantic import BaseModel
from tpbackend.api_models import PlatformTotals, GameTotals


class PublicPlatformModelV2(BaseModel):
    id: int
    abbreviation: str
    name: str | None
    color_primary: str | None
    color_secondary: str | None
    icon: str | None
    created: int
    updated: int


class PublicGameModelV2(BaseModel):
    id: int
    name: str
    steam_id: int | None
    sgdb_id: int | None
    image_url: str | None
    aliases: list[str]
    release_year: int | None
    created: int
    updated: int
    children_ids: list[int]
    parent_id: int | None


class PublicActivityModelV2(BaseModel):
    id: int
    timestamp: int
    seconds: int
    user_id: int
    game_id: int
    platform_id: int
    emulated: bool
    created: int
    updated: int


class GameStatsV2(PublicGameModelV2, GameTotals):
    pass


class PlatformStatsV2(PublicPlatformModelV2, PlatformTotals):
    pass
