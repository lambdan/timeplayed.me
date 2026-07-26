from pydantic import BaseModel, Field

from tpbackend.common.models import BaseTotals
from tpbackend.utils2 import dt_to_ts


class API_Activity(BaseModel):
    id: int
    timestamp: int
    seconds: int
    user_id: int
    game_id: int
    platform_id: int
    emulated: bool
    created: int
    updated: int

    @classmethod
    def from_activity(cls, activity):
        # activity = cast(Activity, activity)
        return cls(
            id=activity.id,
            timestamp=dt_to_ts(activity.timestamp),
            seconds=activity.seconds,
            user_id=activity.user.id,
            game_id=activity.game.id,
            platform_id=activity.platform.id,
            emulated=activity.emulated,
            created=dt_to_ts(activity.created),
            updated=dt_to_ts(activity.updated),
        )


class Total(BaseTotals):
    user_count: int
    platform_count: int
    game_count: int


class API_PostActivity(BaseModel):
    seconds: int = Field(description="Length of the activity in seconds", gt=0)
    game_id: int | None = Field(
        description="ID of the game being played, can be null if igdb_id is provided",
        default=None,
    )
    igdb_id: int | None = Field(
        description="IGDB ID of the game being played, can be null if game_id is provided",
        default=None,
    )
    platform_id: int | None = Field(
        description="ID of platform that was played on. Will default to user's default platform if not provided",
        default=None,
    )
    emulated: bool = Field(
        description="Was activity played in an emulator?", default=False
    )
