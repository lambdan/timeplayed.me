from pydantic import BaseModel, Field

from tpbackend.common.models import BaseTotals
from tpbackend.utils2 import dt_to_ts
from typing import cast


class API_Activity(BaseModel):
    id: int
    started: int = Field(
        description="Timestamp of when the activity started in milliseconds since epoch"
    )
    ended: int = Field(
        description="Timestamp of when the activity ended in milliseconds since epoch"
    )
    timestamp: int = Field(
        description="Same as ended, kept for backwards compatibility", deprecated=True
    )
    seconds: int
    user_id: int
    game_id: int
    platform_id: int
    emulated: bool
    created: int
    updated: int

    @classmethod
    def from_activity(cls, activity):
        # from tpbackend.storage import Activity
        # activity = cast(Activity, activity)
        return cls(
            id=activity.get_id(),
            timestamp=activity.get_timestamp(),
            ended=dt_to_ts(activity.get_ended()),
            started=dt_to_ts(activity.get_started()),
            seconds=activity.get_seconds(),
            user_id=activity.get_user().get_id(),
            game_id=activity.get_game().get_id(),
            platform_id=activity.get_platform().get_id(),
            emulated=activity.get_emulated(),
            created=dt_to_ts(activity.get_created()),
            updated=dt_to_ts(activity.get_updated()),
        )


class API_LiveActivity(BaseModel):
    id: int
    started: int = Field(
        description="Timestamp of when the activity started in milliseconds since epoch"
    )
    user_id: int
    game_id: int
    platform_id: int

    @classmethod
    def from_live_activity(cls, live_activity):
        # import tpbackend.storage as storage
        # live_activity = cast(storage.LiveActivity, live_activity)
        return cls(
            id=live_activity.get_id(),
            started=live_activity.get_started_timestamp(),
            user_id=live_activity.get_user().get_id(),
            game_id=live_activity.get_game().get_id(),
            platform_id=live_activity.get_platform().get_id(),
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


class API_PostLiveActivity(BaseModel):
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
