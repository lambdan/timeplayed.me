from discord.utils import P
from tpbackend.api_v2_models import (
    GameStatsV2,
    PlatformStatsV2,
    PublicGameModelV2,
    PublicPlatformModelV2,
)
from tpbackend.utils import (
    search_games,
)
from tpbackend.utils2 import clamp, validateTS, parse_csv
from tpbackend.api_v2.types import PATH_IDS_CSV, QUERY_TS_BEFORE, QUERY_TS_AFTER
from tpbackend.storage.storage_v2 import (
    Activity,
    Game,
)
import logging
from tpbackend.api_v2.responses import bad_request

from fastapi import APIRouter

logger = logging.getLogger("api_v2")
router = APIRouter()


ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712

IDS_CSV = PATH_IDS_CSV
TS_QUERY_BEFORE = QUERY_TS_BEFORE
TS_QUERY_AFTER = QUERY_TS_AFTER


################ HELPERS ##################


##############
# Games
#############


@router.get("/games", tags=["games"], response_model=list[PublicGameModelV2])
def get_all_games(
    offset=0,
    limit=25,
    search: str | None = None,
    userId: int | None = None,
    platformId: int | None = None,
) -> list[PublicGameModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    res = []
    if search:
        if len(search) < 2:
            return bad_request("Search query must be at least 2 characters long")
        raw = search_games(
            query=search,
            limit=limit,
            offset=offset,
            userId=userId,
            platformId=platformId,
        )
        for g in raw:
            res.append(g.get_api_v2_model())

    return res


@router.get("/games/stats", tags=["games", "stats"], response_model=list[GameStatsV2])
def get_all_games_stats(
    offset=0,
    limit=25,
    userId: int | None = None,
    platformId: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    search: str | None = None,
) -> list[GameStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    gids = []

    if search:
        if len(search) < 2:
            return bad_request("Search query must be at least 2 characters long")
        results = search_games(
            query=search,
            limit=limit,
            offset=offset,
            userId=userId,
            platformId=platformId,
        )
        for r in results:
            gids.append(r.get_id())
    else:
        all_games = Game.select().order_by(Game.id.asc()).offset(offset).limit(limit)
        for g in all_games:
            gids.append(g.id)
    gids_str = ",".join(str(gid) for gid in gids)
    return []


@router.get(
    "/games/{game_ids}/stats",
    tags=["games", "stats"],
    response_model=list[GameStatsV2],
)
def get_games_stats(
    game_ids: int | str = IDS_CSV,
    userId: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    platformId: int | None = None,
) -> list[GameStatsV2]:
    gids = parse_csv(game_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 games at once")

    return []


@router.get("/games/{ids}", tags=["games"], response_model=list[PublicGameModelV2])
def get_games(ids: int | str = IDS_CSV) -> list[PublicGameModelV2]:
    gids = parse_csv(ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 games at once")
    res = []
    return res


##############
# Platforms
##############


@router.get(
    "/platforms/{platform_ids}/stats",
    tags=["platforms"],
    response_model=list[PlatformStatsV2],
)
def get_platforms_stats(
    platform_ids: int | str = IDS_CSV,
    userId: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    gameId: int | None = None,
) -> list[PlatformStatsV2]:
    res = []
    pids = parse_csv(platform_ids)
    if len(pids) > 100:
        return bad_request("Cannot request more than 100 platforms at once")

    return res


@router.get(
    "/platforms/stats",
    tags=["platforms", "stats"],
    response_model=list[PlatformStatsV2],
)
def get_all_platforms_stats(
    offset=0,
    limit=25,
    userId: int | None = None,
    gameId: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
) -> list[PlatformStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)
    return []


@router.get(
    "/platforms/{ids}", tags=["platforms"], response_model=list[PublicPlatformModelV2]
)
def get_platforms(ids: int | str = IDS_CSV) -> list[PublicPlatformModelV2]:
    pids = parse_csv(ids)
    if len(pids) > 100:
        return bad_request("Cannot request more than 100 platforms at once")
    res = []
    return res


@router.get(
    "/platforms", tags=["platforms"], response_model=list[PublicPlatformModelV2]
)
def get_all_platforms(
    offset=0,
    limit=25,
) -> list[PublicPlatformModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    res = []
    return res
