from typing import Literal

from pydantic import BaseModel, Field
from tpbackend.utils2 import dt_to_ts
from tpbackend.common.models import BaseTotals
from tpbackend.storage import User

# what Discord PC activity counts as, the abbreviations of the pc (unknown OS)/windows/mac/linux platforms
PCPlatform = Literal["pc", "win", "mac", "linux"]


class UserTotals(BaseTotals):
    game_count: int = Field(description="Total number of unique games")
    platform_count: int = Field(description="Total number of unique platforms")


class API_User(BaseModel):
    id: int
    discord_id: str | None = Field(description="null for anonymous users")
    name: str = Field(
        description="Discord username typically, 'User <id>' for anonymous users"
    )
    display_name: str = Field(description="Discord display name")
    created: int
    updated: int

    @classmethod
    def from_user(cls, user: User) -> "API_User":
        name = user.get_name()
        display_name = user.get_display_name()
        discord_id = user.get_discord_id()
        if user.is_anonymous():
            name = f"User {user.get_id()}"
            display_name = name
            discord_id = None
        return cls(
            id=user.get_id(),
            discord_id=discord_id,
            name=name,
            display_name=display_name,
            created=dt_to_ts(user.created),  # type: ignore
            updated=dt_to_ts(user.updated),  # type: ignore
        )


class API_AuthenticatedUser(API_User):
    permissions: list[str]
    pc_platform: str = Field(
        description="What PC activity counts as (pc/win/mac/linux)"
    )

    @classmethod
    def from_user(cls, user: User):
        return cls(
            **API_User.from_user(user).model_dump(),
            permissions=user.get_permissions(),
            pc_platform=user.get_pc_platform(),
        )


class API_PutSettings(BaseModel):
    """leave out what shouldn't change"""

    pc_platform: PCPlatform | None = Field(
        default=None, description="What PC activity counts as"
    )
    show_nsfw: bool | None = Field(
        default=None, description="Show NSFW game titles and covers"
    )
    anonymous: bool | None = Field(
        default=None,
        description="Hide name, avatar and Discord ID on the site (an admin can force it on)",
    )
    hide_playing: bool | None = Field(
        default=None, description="Leave the user out of now playing"
    )
    private: bool | None = Field(
        default=None,
        description="Only the user sees their page, their activity and stats are left out everywhere else",
    )
    move_pc_activity: bool | None = Field(
        default=None,
        description="Also move the user's activity on 'pc' (unknown OS) to the new pc_platform, needs manual_activity",
    )


class API_UserWithStats(API_User):
    stats: UserTotals

    @classmethod
    def from_user(cls, user):
        return cls(
            **API_User.from_user(user).model_dump(),
            stats=UserTotals(
                seconds=user.total_seconds,
                activity_count=user.activity_count,
                game_count=user.game_count,
                platform_count=user.platform_count,
                last_activity=(
                    dt_to_ts(user.last_activity) if user.last_activity else None
                ),
                first_activity=(
                    dt_to_ts(user.first_activity) if user.first_activity else None
                ),
            ),
        )
