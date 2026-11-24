from typing import Literal

from pydantic import BaseModel, Field
from tpbackend.utils2 import dt_to_ts
from tpbackend.common.models import BaseTotals
from tpbackend.permissions import Permission

# what Discord PC activity counts as, the abbreviations of the pc (unknown OS)/windows/mac/linux platforms
PCPlatform = Literal["pc", "win", "mac", "linux"]


class UserTotals(BaseTotals):
    game_count: int = Field(description="Total number of unique games")
    platform_count: int = Field(description="Total number of unique platforms")


class API_User(BaseModel):
    id: int
    discord_id: str | None
    name: str = Field("Discord username typically")
    display_name: str = Field("Discord display name")
    created: int
    updated: int

    @classmethod
    def from_user(cls, user):
        name = user.name
        display_name = user.get_display_name()
        if not user.has_permission(Permission.SHOW_NAME):
            name = f"User {user.id}"
            display_name = name
        return cls(
            id=user.id,
            discord_id=user.discord_id,
            name=name,
            display_name=display_name,
            created=dt_to_ts(user.created),
            updated=dt_to_ts(user.updated),
        )


class API_AuthenticatedUser(API_User):
    permissions: list[str]
    pc_platform: str = Field(
        description="What PC activity counts as (pc/win/mac/linux)"
    )

    @classmethod
    def from_user(cls, user):
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
