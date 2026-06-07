from pydantic import BaseModel, Field
from tpbackend.api_models import PlatformTotals, UserTotals, GameTotals


class PaginatedResponseV2(BaseModel):
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Offset for pagination")
    limit: int = Field(description="Limit for pagination")


####################
# Public versions of db models
###################


class PublicPlatformModelV2(BaseModel):
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


class PublicUserModelV2(BaseModel):
    id: int
    discord_id: str | None
    name: str
    default_platform_id: int
    created: int
    updated: int


class PublicGameModelV2(BaseModel):
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
    children_ids: list[int] = Field(description="List of child game IDs")
    parent_id: int | None = Field(description="Parent game ID. Null if no parent.")


class PublicActivityModelV2(BaseModel):
    id: int = Field(description="ID for the activity")
    timestamp: int = Field(description="Timestamp (in milliseconds) for the activity")
    seconds: int = Field(description="Duration of the activity in seconds")
    user_id: int
    game_id: int
    platform_id: int
    emulated: bool = Field(description="True if the activity was played in an emulator")
    created: int = Field(
        description="Timestamp (in milliseconds) for the creation of the activity"
    )
    updated: int = Field(
        description="Timestamp (in milliseconds) for the last update of the activity"
    )


class GameStatsV2(PublicGameModelV2, GameTotals):
    pass


class PlatformStatsV2(PublicPlatformModelV2, PlatformTotals):
    pass


class UserStatsV2(PublicUserModelV2, UserTotals):
    pass
