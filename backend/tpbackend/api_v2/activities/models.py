from pydantic import BaseModel

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
