from pydantic import BaseModel
from tpbackend.api_models import PlatformTotals, GameTotals


class PublicPlatformModelV2(BaseModel):
    id: int
    abbreviation: str
    name: str | None
    color_primary: str | None
    color_secondary: str | None
    icon: str | None
    created: int
    updated: int


class PlatformStatsV2(PublicPlatformModelV2, PlatformTotals):
    pass
