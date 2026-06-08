from typing import Literal
from pydantic import BaseModel, Field
from tpbackend.api_v2.models import BaseTotals


class GameTotals(BaseTotals):
    user_count: int = Field(description="Total number of unique users")
    platform_count: int = Field(description="Total number of unique platforms")
    playtime_secs_excl_children: int
    activity_count_excl_children: int


class PlatformTotals(BaseTotals):
    user_count: int = Field(description="Total number of unique users")
    game_count: int = Field(description="Total number of unique games")


class PaginatedResponse(BaseModel):
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Offset for pagination")
    limit: int = Field(description="Limit for pagination")


####################
# Public versions of db models
###################


class PublicPlatformModel(BaseModel):
    id: int = Field(description="ID for the platform")
    abbreviation: str = Field(description="Abbreviation for the platform")
    name: str | None = Field(description="Name of the platform")
    color_primary: str | None = Field(description="Primary color for the platform")
    color_secondary: str | None = Field(description="Secondary color for the platform")
    icon: str | None = Field(description="Icon name")
    created: int = Field(
        description="Timestamp (in milliseconds) for the creation of the platform"
    )
    updated: int = Field(
        description="Timestamp (in milliseconds) for the last update of the platform"
    )


class PublicUserModel(BaseModel):
    id: int = Field(description="ID of the user")
    discord_id: str | None = Field(description="Discord ID of the user")
    name: str = Field(description="Name of the user")
    default_platform: PublicPlatformModel = Field(description="User's default platform")
    created: int = Field(
        description="Timestamp (in milliseconds) for the creation of the user"
    )
    updated: int = Field(
        description="Timestamp (in milliseconds) for the last update of the user"
    )


class PublicGameModel(BaseModel):
    id: int = Field(description="ID for the game")
    name: str = Field(description="Name of the game")
    steam_id: int | None = Field(description="Steam ID for the game")
    sgdb_id: int | None = Field(
        description="SGDB ID for the game. Null if not set. 0 if game is not in SGDB."
    )
    image_url: str | None = Field(description="Image URL for the game")
    aliases: list[str] = Field(description="List of aliases for the game")
    release_year: int | None = Field(description="Release year of the game")
    created: int = Field(
        description="Timestamp (in milliseconds) for the creation of the game"
    )
    updated: int = Field(
        description="Timestamp (in milliseconds) for the last update of the game"
    )
    children: list[int] = Field(description="List of child game IDs")
    parent_id: int | None = Field(description="Parent game ID. Null if no parent.")


class PublicActivityModel(BaseModel):
    id: int = Field(description="ID for the activity")
    timestamp: int = Field(description="Timestamp (in milliseconds) for the activity")
    seconds: int = Field(description="Duration of the activity in seconds")
    user: PublicUserModel = Field(description="User associated with the activity")
    game: PublicGameModel = Field(description="Game associated with the activity")
    platform: PublicPlatformModel = Field(
        description="Platform associated with the activity"
    )
    emulated: bool = Field(description="True if the activity was played in an emulator")
    created: int = Field(
        description="Timestamp (in milliseconds) for the creation of the activity"
    )
    updated: int = Field(
        description="Timestamp (in milliseconds) for the last update of the activity"
    )
