from tpbackend.activity.query import ActivityQuery
from tpbackend.platform.models import API_PlatformWithStats, API_Platform
from tpbackend.platform.query import PlatformStatsQuery, PlatformQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.api.responses import bad_request, not_found
import logging
from fastapi import APIRouter, Path
from tpbackend.api.params import (
    AscDescOrder,
    path_csv,
    path_id,
    query_search,
    query_ts,
    query_id,
    sorts,
    offset,
    limit,
)

logger = logging.getLogger("platforms-routes")
router = APIRouter()


def __get_platforms_stats(
    pids: list[int] | None = None,
    before=None,
    after=None,
    user_id: int | None = None,
    game_id: int | None = None,
    sort="id",
    order="asc",
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
        query = ActivityQuery.game(query, game_id)

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
    platform_id=path_id("platform"),
    before=query_ts("before"),
    after=query_ts("after"),
    user=query_id("user"),
    game=query_id("game"),
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
    platform_ids=path_csv("platform ids"),
    before=query_ts("before"),
    after=query_ts("after"),
    user=query_id("user"),
    game=query_id("game"),
    sort=sorts(list(PlatformStatsQuery.SORTS.keys()), "id"),
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
    offset=offset(),
    limit=limit(),
    user=query_id("user"),
    game=query_id("game"),
    before=query_ts("before"),
    after=query_ts("after"),
    sort=sorts(list(PlatformStatsQuery.SORTS.keys()), "playtime"),
    order: AscDescOrder = "desc",
    search=query_search("platforms"),
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
    sort="id",
    order="asc",
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
    platform_ids=path_csv("platform ids"),
    sort=sorts(list(PlatformQuery.SORTS.keys()), "id"),
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
    offset=offset(),
    limit=limit(),
    sort=sorts(list(PlatformQuery.SORTS.keys()), "id"),
    order: AscDescOrder = "asc",
    search=query_search("platforms"),
) -> list[API_Platform]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_platforms(
        sort=sort, order=order, offset=offset, limit=limit, search=search
    )
