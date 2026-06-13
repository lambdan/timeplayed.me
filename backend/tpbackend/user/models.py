from pydantic import BaseModel, Field
from tpbackend.utils2 import dt_to_ts
from tpbackend.common.models import BaseTotals


class UserTotals(BaseTotals):
    game_count: int = Field(description="Total number of unique games")
    platform_count: int = Field(description="Total number of unique platforms")


class API_User(BaseModel):
    id: int
    discord_id: str | None
    name: str
    default_platform_id: int
    created: int
    updated: int

    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            discord_id=user.discord_id,
            name=user.name,
            default_platform_id=user.default_platform_id,
            created=dt_to_ts(user.created),
            updated=dt_to_ts(user.updated),
        )


class API_UserWithStats(API_User):
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
                last_activity=(
                    dt_to_ts(user.last_activity) if user.last_activity else None
                ),
            ),
        )
