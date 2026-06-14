from tpbackend.activity.query import ActivityQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.user.query import UserStatsQuery, UserQuery
from tpbackend.user.models import API_UserWithStats, API_User
from tpbackend.api.responses import bad_request, not_found
import logging
from fastapi import APIRouter, Path
from tpbackend.api.params import (
    path_csv,
    query_ts,
    AscDescOrder,
    path_id,
    query_id,
    query_csv,
    query_search,
    sorts,
    offset,
    limit,
)

logger = logging.getLogger("users-routes")
router = APIRouter()


def __get_users_stats(
    uids: list[int] | None = None,
    before: int | None = None,
    after: int | None = None,
    game_id: int | None = None,
    platform_id: int | None = None,
    sort="id",
    order="asc",
    offset=None,
    limit=None,
    search="",
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

    if search:
        query = UserQuery.search(query, search=search)

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
)
def get_single_user_stats(
    user_id: int,
    before=query_ts("before"),
    after=query_ts("after"),
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
)
def get_many_users_stats(
    user_ids=path_csv("user ids"),
    before=query_ts("before"),
    after=query_ts("after"),
    game=query_id("game"),
    platform=query_id("platform"),
    sort=sorts(list(UserStatsQuery.SORTS.keys()), "id"),
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
)
def get_users_stats(
    offset=offset(),
    limit=limit(),
    game=query_id("game"),
    platform=query_id("platform"),
    before=query_ts("before"),
    after=query_ts("after"),
    sort=sorts(list(UserStatsQuery.SORTS.keys()), "playtime"),
    order: AscDescOrder = "desc",
    search=query_search("users"),
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
        search=search,
    )


################################################
############# plain user (no stats) ############
################################################


def __get_users(
    ids: list[int] | None = None,
    sort="id",
    order="asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
) -> list[API_User]:
    query = UserQuery.base()
    if search:
        query = UserQuery.search(query, search=search)
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
)
def get_single_user(user_id: int) -> API_User:
    x = __get_users(ids=[int(user_id)])
    if len(x) == 0:
        return not_found("User not found")
    return x[0]


@router.get(
    "/users/{user_ids}",
    tags=["users"],
    response_model=list[API_User],
)
def get_many_users(
    user_ids=path_csv("user ids"),
    sort=sorts(list(UserQuery.SORTS.keys()), "id"),
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
)
def get_users(
    offset=offset(),
    limit=offset(),
    sort=sorts(list(UserQuery.SORTS.keys()), "id"),
    order: AscDescOrder = "asc",
    search=query_search("users"),
) -> list[API_User]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_users(
        sort=sort, order=order, offset=offset, limit=limit, search=search
    )
