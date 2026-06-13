from tpbackend.activity.query import ActivityQuery
from tpbackend.platform.models import API_PlatformWithStats, API_Platform
from tpbackend.platform.query import PlatformStatsQuery, PlatformQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.http_responses import bad_request, not_found
import logging
from fastapi import APIRouter, Path
from tpbackend.common.types import (
    QUERY_TS_BEFORE,
    QUERY_TS_AFTER,
    AscDescOrder,
)

logger = logging.getLogger("platforms-routes")
router = APIRouter()


def __get_platforms_stats(
    pids: list[int] | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user_id: int | None = None,
    game_id: int | None = None,
    sort: PlatformStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
) -> list[API_PlatformWithStats]:
    bf = parseTS(before)
    af = parseTS(after)

    query = PlatformStatsQuery.base()
    if pids and len(pids) > 0:
        if len(pids) > 100:
            return bad_request("Cannot request more than 100 platforms at once")
        query = PlatformStatsQuery.apply_ids(query, pids)

    if bf:
        query = ActivityQuery.before(query, bf)

    if af:
        query = ActivityQuery.after(query, af)

    if user_id:
        query = ActivityQuery.user(query, user_id)

    if game_id:
        query = ActivityQuery.platform(query, game_id)

    if search:
        query = PlatformQuery.search(query, search=search)

    query = PlatformStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, int(offset)))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    return [API_PlatformWithStats.from_platform(platform) for platform in query]


@router.get(
    "/platform-stats/{platform_id}",
    tags=["platforms", "stats"],
    response_model=API_PlatformWithStats,
)
def get_single_platform_stats(
    platform_id: int,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    game: int | None = None,
) -> API_PlatformWithStats:
    x = __get_platforms_stats(
        pids=[int(platform_id)],
        before=before,
        after=after,
        user_id=user,
        game_id=game,
    )
    if len(x) == 0:
        return not_found("Platform not found")
    return x[0]


@router.get(
    "/platforms-stats/{platform_ids}",
    response_model=list[API_PlatformWithStats],
    tags=["platforms", "stats"],
)
def get_many_platforms_stats(
    platform_ids: str = Path(description="Comma-separated list of platform IDs"),
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    game: int | None = None,
    sort: PlatformStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_PlatformWithStats]:
    pids = parse_csv(platform_ids)
    return __get_platforms_stats(
        pids=pids,
        before=before,
        after=after,
        user_id=user,
        game_id=game,
        sort=sort,
        order=order,
    )


@router.get(
    "/platforms-stats",
    tags=["platforms", "stats"],
    response_model=list[API_PlatformWithStats],
)
def get_platforms_stats(
    offset=0,
    limit=25,
    user: int | None = None,
    game: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    sort: PlatformStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
    search="",
) -> list[API_PlatformWithStats]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_platforms_stats(
        before=before,
        after=after,
        user_id=user,
        game_id=game,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
        search=search,
    )


################################################
############# plain platform (no stats) ############
################################################


def __get_platforms(
    ids: list[int] | None = None,
    sort: PlatformQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
) -> list[API_Platform]:
    query = PlatformQuery.base()
    if search:
        query = PlatformQuery.search(query, search=search)
    if ids and len(ids) > 0:
        query = PlatformQuery.apply_ids(query=query, platform_ids=ids)
    query = PlatformQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, offset))
    if limit:
        query = query.limit(clamp(limit, 1, 100))

    return [API_Platform.from_platform(g) for g in query]


@router.get(
    "/platform/{platform_id}",
    tags=["platforms"],
    response_model=API_Platform,
)
def get_single_platform(platform_id: int) -> API_Platform:
    x = __get_platforms(ids=[int(platform_id)])
    if len(x) == 0:
        return not_found("Platform not found")
    return x[0]


@router.get(
    "/platforms/{platform_ids}",
    tags=["platforms"],
    response_model=list[API_Platform],
)
def get_many_platforms(
    platform_ids: str = Path(description="Comma-separated list of platform IDs"),
    sort: PlatformQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_Platform]:
    pids = parse_csv(platform_ids)
    if len(pids) > 100:
        return bad_request("Cannot request more than 100 platforms at once")
    return __get_platforms(
        ids=pids,
        sort=sort,
        order=order,
    )


@router.get(
    "/platforms",
    tags=["platforms"],
    response_model=list[API_Platform],
)
def get_platforms(
    offset=0,
    limit=25,
    sort: PlatformQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    search="",
) -> list[API_Platform]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_platforms(
        sort=sort, order=order, offset=offset, limit=limit, search=search
    )
