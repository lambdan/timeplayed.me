from tpbackend.api_v2.activities.query import ActivityQuery
from tpbackend.api_v2.platforms.models import PlatformStatsV2, PublicPlatformModelV2
from tpbackend.api_v2.platforms.query import PlatformStatsQuery, PlatformQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.api_v2.responses import bad_request, not_found
import logging
from fastapi import APIRouter
from tpbackend.api_v2.types import (
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
) -> list[PlatformStatsV2]:
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

    query = PlatformStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, int(offset)))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    return [PlatformStatsV2.from_platform(platform) for platform in query]


@router.get(
    "/platform-stats/{platform_id}",
    tags=["platforms", "stats"],
    response_model=PlatformStatsV2,
    description="Get a platform, including stats, by id",
)
def get_platform_stats(
    platform_id: int,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    game: int | None = None,
) -> PlatformStatsV2:
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
    response_model=list[PlatformStatsV2],
    tags=["platforms", "stats"],
    description="Get many platforms, including stats, by id (comma separated). Max 100 at once.",
)
def get_platforms_stats(
    platform_ids: str,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    game: int | None = None,
    sort: PlatformStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PlatformStatsV2]:
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
    response_model=list[PlatformStatsV2],
    description="Get all platforms, including stats",
)
def get_all_platforms_stats(
    offset=0,
    limit=25,
    user: int | None = None,
    game: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    sort: PlatformStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[PlatformStatsV2]:
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
) -> list[PublicPlatformModelV2]:
    query = PlatformQuery.base()
    if ids and len(ids) > 0:
        query = PlatformQuery.apply_ids(query=query, platform_ids=ids)
    query = PlatformQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, offset))
    if limit:
        query = query.limit(clamp(limit, 1, 100))
    return [PublicPlatformModelV2.from_platform(g) for g in query]


@router.get(
    "/platform/{platform_id}",
    tags=["platforms"],
    response_model=PublicPlatformModelV2,
    description="Get a platform by id",
)
def get_platform_by_id(platform_id: int) -> PublicPlatformModelV2:
    x = __get_platforms(ids=[int(platform_id)])
    if len(x) == 0:
        return not_found("Platform not found")
    return x[0]


@router.get(
    "/platforms/{platform_ids}",
    tags=["platforms"],
    response_model=list[PublicPlatformModelV2],
    description="Get many platforms by id (comma separated). Max 100 at once.",
)
def get_platforms_by_ids(
    platform_ids: str,
    sort: PlatformQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicPlatformModelV2]:
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
    response_model=list[PublicPlatformModelV2],
    description="Get all platforms",
)
def get_all_platforms(
    offset=0,
    limit=25,
    sort: PlatformQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicPlatformModelV2]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_platforms(
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
