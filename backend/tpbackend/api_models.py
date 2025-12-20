from typing import Literal
from pydantic import BaseModel, Field


class Totals(BaseModel):
    playtime_secs: int = Field(description="Total playtime in seconds")
    activity_count: int = Field(description="Total number of activities")
    user_count: int = Field(description="Total number of unique users")
    game_count: int = Field(description="Total number of unique games")
    platform_count: int = Field(description="Total number of unique platforms")


class PaginatedResponse(BaseModel):
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Offset for pagination")
    limit: int = Field(description="Limit for pagination")


####################
# Public versions of db models
###################


class DiscordAvatarModel(BaseModel):
    url: str | None = Field(description="URL for the avatar image")


class PublicPlatformModel(BaseModel):
    id: int = Field(description="ID for the platform")
    abbreviation: str = Field(description="Abbreviation for the platform")
    name: str | None = Field(description="Name of the platform")


class PublicUserModel(BaseModel):
    id: str = Field(description="Discord ID for the user")
    name: str = Field(description="Name of the user")
    default_platform: PublicPlatformModel = Field(description="User's default platform")


class PublicGameModel(BaseModel):
    id: int = Field(description="ID for the game")
    name: str = Field(description="Name of the game")
    steam_id: int | None = Field(description="Steam ID for the game")
    sgdb_id: int | None = Field(description="SGDB ID for the game")
    image_url: str | None = Field(description="Image URL for the game")
    aliases: list[str] = Field(description="List of aliases for the game")
    release_year: int | None = Field(description="Release year of the game")


class PublicActivityModel(BaseModel):
    id: int = Field(description="ID for the activity")
    timestamp: int = Field(description="Timestamp for the activity")
    seconds: int = Field(description="Duration of the activity in seconds")
    user: PublicUserModel = Field(description="User associated with the activity")
    game: PublicGameModel = Field(description="Game associated with the activity")
    platform: PublicPlatformModel = Field(
        description="Platform associated with the activity"
    )


class GameOrPlatformStats(BaseModel):
    totals: Totals
    oldest_activity: PublicActivityModel | None
    newest_activity: PublicActivityModel | None
    percent: float = Field(description="Share of total playtime")


class UserWithStats(BaseModel):
    user: PublicUserModel
    oldest_activity: PublicActivityModel
    newest_activity: PublicActivityModel
    totals: Totals


####################
# With stats
####################


class GameWithStats(GameOrPlatformStats):
    game: PublicGameModel


class PlatformWithStats(GameOrPlatformStats):
    platform: PublicPlatformModel


################
# Paginated Responses
################


class PaginatedPlatformsWithStats(PaginatedResponse):
    data: list[PlatformWithStats]


class PaginatedGames(PaginatedResponse):
    data: list[PublicGameModel]


class PaginatedGameWithStats(PaginatedResponse):
    data: list[GameWithStats]


class PaginatedActivities(PaginatedResponse):
    data: list[PublicActivityModel]
    order: Literal["desc", "asc"]


class PaginatedUserWithStats(PaginatedResponse):
    data: list[UserWithStats]
