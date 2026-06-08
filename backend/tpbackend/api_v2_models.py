from datetime import datetime
from pydantic import BaseModel
from tpbackend.api_models import PlatformTotals, UserTotals, GameTotals
from tpbackend.utils2 import dt_to_ts


class PublicPlatformModelV2(BaseModel):
    id: int
    abbreviation: str
    name: str | None
    color_primary: str | None
    color_secondary: str | None
    icon: str | None
    created: int
    updated: int


class PublicUserModelV2(BaseModel):
    id: int
    discord_id: str | None
    name: str
    default_platform_id: int
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


class UserStatsV2(PublicUserModelV2):
    stats: UserTotals

    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            discord_id=user.discord_id,
            name=user.name,
            default_platform_id=user.default_platform_id,
            created=dt_to_ts(user.created),
            updated=dt_to_ts(user.updated),
            stats=UserTotals(
                seconds=user.total_seconds,
                activity_count=user.activity_count,
                game_count=user.game_count,
                platform_count=user.platform_count,
                last_activity=dt_to_ts(user.last_activity),
            ),
        )
