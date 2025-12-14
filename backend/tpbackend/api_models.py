from datetime import datetime
from typing import Literal
from pydantic import BaseModel


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


class SummarizedUserResponse(BaseModel):
    user: PublicUserModel
    last_played: int | None = None
    total_activities: int
    total_playtime: int


class PaginatedUsers(PaginatedResponse):
    data: list[SummarizedUserResponse]


class TotalsResponse(BaseModel):
    total_playtime: int
    activities: int
    users: int
    games: int
    platforms: int


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


class PaginatedActivities(PaginatedResponse):
    data: list[PublicActivityModel]
    order: Literal["desc", "asc"]


class GameWithStats(BaseModel):
    game: PublicGameModel
    last_played: int | None
    total_sessions: int
    total_playtime: int


class PaginatedGameWithStats(PaginatedResponse):
    data: list[GameWithStats]


class GameStatsResponse(BaseModel):
    total_playtime: int
    activity_count: int
    platform_count: int
    player_count: int
    oldest_activity: PublicActivityModel | None
    newest_activity: PublicActivityModel | None


class PlatformWithStats(BaseModel):
    platform: PublicPlatformModel
    last_played: int | None
    total_sessions: int
    total_playtime: int
    percent: float


class PaginatedPlatforms(PaginatedResponse):
    data: list[PlatformWithStats]
