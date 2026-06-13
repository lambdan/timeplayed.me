from pydantic import BaseModel
from tpbackend.common.models import BaseTotals
from tpbackend.utils2 import dt_to_ts


class PlatformTotals(BaseTotals):
    user_count: int
    game_count: int


class API_Platform(BaseModel):
    id: int
    abbreviation: str
    name: str | None
    color_primary: str | None
    color_secondary: str | None
    icon: str | None
    created: int
    updated: int

    @classmethod
    def from_platform(cls, platform):
        return cls(
            id=platform.id,
            abbreviation=platform.abbreviation,
            name=platform.name,
            color_primary=platform.color_primary,
            color_secondary=platform.color_secondary,
            icon=platform.icon,
            created=dt_to_ts(platform.created),
            updated=dt_to_ts(platform.updated),
        )


class API_PlatformWithStats(API_Platform):
    stats: PlatformTotals

    @classmethod
    def from_platform(cls, platform):
        return cls(
            id=platform.id,
            abbreviation=platform.abbreviation,
            name=platform.name,
            color_primary=platform.color_primary,
            color_secondary=platform.color_secondary,
            icon=platform.icon,
            created=dt_to_ts(platform.created),
            updated=dt_to_ts(platform.updated),
            stats=PlatformTotals(
                seconds=platform.total_seconds,
                activity_count=platform.activity_count,
                user_count=platform.user_count,
                game_count=platform.game_count,
                last_activity=(
                    dt_to_ts(platform.last_activity) if platform.last_activity else None
                ),
            ),
        )
