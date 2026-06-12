from tpbackend.api_v2.activities.query import ActivityQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.api_v2.users.query import UserStatsQuery, UserQuery
from tpbackend.api_v2.users.models import API_UserWithStats, API_User
from tpbackend.api_v2.responses import bad_request, not_found
import logging
from fastapi import APIRouter, Path
from tpbackend.api_v2.types import (
    QUERY_TS_BEFORE,
    QUERY_TS_AFTER,
    AscDescOrder,
)

logger = logging.getLogger("users-routes")
router = APIRouter()


def __get_users_stats(
    uids: list[int] | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    game_id: int | None = None,
    platform_id: int | None = None,
    sort: UserStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    offset: int | None = None,
    limit: int | None = None,
) -> list[API_UserWithStats]:
    bf = parseTS(before)
    af = parseTS(after)

    query = UserStatsQuery.base()
    if uids and len(uids) > 0:
        if len(uids) > 100:
            return bad_request("Cannot request more than 100 users at once")
        query = UserStatsQuery.apply_ids(query, uids)

    if bf:
        query = ActivityQuery.before(query, bf)

    if af:
        query = ActivityQuery.after(query, af)

    if game_id:
        query = ActivityQuery.game(query, game_id)

    if platform_id:
        query = ActivityQuery.platform(query, platform_id)

    query = UserStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, offset))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    # print("__get_users_stats QUERY", query.sql())
    return [API_UserWithStats.from_user(user) for user in query]


@router.get(
    "/user-stats/{user_id}",
    tags=["users", "stats"],
    response_model=API_UserWithStats,
    description="Get a single user, including stats, by id.",
)
def get_user_stats(
    user_id: int,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    game: int | None = None,
    platform: int | None = None,
) -> API_UserWithStats:
    x = __get_users_stats(
        uids=[int(user_id)],
        before=before,
        after=after,
        game_id=game,
        platform_id=platform,
    )
    if len(x) == 0:
        return not_found("User not found")
    return x[0]


@router.get(
    "/users-stats/{user_ids}",
    response_model=list[API_UserWithStats],
    tags=["users", "stats"],
    description="Get many users, including stats, by id (comma separated). Max 100 at once.",
)
def get_users_stats(
    user_ids: str,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    game: int | None = None,
    platform: int | None = None,
    sort: UserStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_UserWithStats]:
    uids = parse_csv(user_ids)
    return __get_users_stats(
        uids=uids,
        before=before,
        after=after,
        game_id=game,
        platform_id=platform,
        sort=sort,
        order=order,
    )


@router.get(
    "/users-stats",
    tags=["users", "stats"],
    response_model=list[API_UserWithStats],
    description="Get users, including stats, with optional filters and pagination.",
)
def get_all_users_stats(
    offset=0,
    limit=25,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    sort: UserStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[API_UserWithStats]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_users_stats(
        before=before,
        after=after,
        game_id=game,
        platform_id=platform,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )


################################################
############# plain user (no stats) ############
################################################


def __get_users(
    ids: list[int] | None = None,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    offset: int | None = None,
    limit: int | None = None,
) -> list[API_User]:
    query = UserQuery.base()
    if ids and len(ids) > 0:
        query = UserQuery.apply_ids(query=query, user_ids=ids)
    query = UserQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, int(offset)))
    if limit:
        query = query.limit(clamp(limit, 1, 100))
    return [API_User.from_user(u) for u in query]


@router.get(
    "/user/{user_id}",
    tags=["users"],
    response_model=API_User,
    description="Get a single user by id.",
)
def get_user_by_id(user_id: int) -> API_User:
    x = __get_users(ids=[int(user_id)])
    if len(x) == 0:
        return not_found("User not found")
    return x[0]


@router.get(
    "/users/{user_ids}",
    tags=["users"],
    response_model=list[API_User],
    description="Get many users by id (comma separated). Max 100 at once.",
)
def get_users_by_ids(
    user_ids: str,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_User]:
    gids = parse_csv(user_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 users at once")
    return __get_users(
        ids=gids,
        sort=sort,
        order=order,
    )


@router.get(
    "/users",
    tags=["users"],
    response_model=list[API_User],
    description="Get users with optional filters and pagination.",
)
def get_all_users(
    offset=0,
    limit=25,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_User]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_users(
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
