from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class Totals(BaseModel):
    playtime_secs: int
    activity_count: int
    user_count: int
    game_count: int
    platform_count: int


class PaginatedResponse(BaseModel):
    total: int
    offset: int
    limit: int


class PublicPlatformModel(BaseModel):
    id: int
    abbreviation: str
    name: str | None


class PublicUserModel(BaseModel):
    id: str  # hmm
    name: str
    default_platform: PublicPlatformModel


class PublicGameModel(BaseModel):
    id: int
    name: str
    steam_id: int | None
    sgdb_id: int | None
    image_url: str | None
    aliases: list[str]
    release_year: int | None


class PaginatedGames(PaginatedResponse):
    data: list[PublicGameModel]


class PublicActivityModel(BaseModel):
    id: int
    timestamp: int
    user: PublicUserModel
    game: PublicGameModel
    seconds: int
    platform: PublicPlatformModel


class GameOrPlatformStats(BaseModel):
    totals: Totals
    oldest_activity: PublicActivityModel | None
    newest_activity: PublicActivityModel | None
    percent: float


class UserWithStats(BaseModel):
    user: PublicUserModel
    oldest_activity: PublicActivityModel
    newest_activity: PublicActivityModel
    totals: Totals


class PaginatedSummarizedUsers(PaginatedResponse):
    data: list[UserWithStats]


class PaginatedActivities(PaginatedResponse):
    data: list[PublicActivityModel]
    order: Literal["desc", "asc"]


class GameWithStats(GameOrPlatformStats):
    game: PublicGameModel


class PaginatedGameWithStats(PaginatedResponse):
    data: list[GameWithStats]


# class GameStatsResponse(BaseModel):
#     total_playtime: int
#     activity_count: int
#     platform_count: int
#     player_count: int
#     oldest_activity: PublicActivityModel | None
#     newest_activity: PublicActivityModel | None


class PlatformWithStats(GameOrPlatformStats):
    platform: PublicPlatformModel


class PaginatedPlatforms(PaginatedResponse):
    data: list[PlatformWithStats]
