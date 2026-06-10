from typing import Literal, cast
from tpbackend.utils2 import clamp, validateTS, parseTS, parse_csv
from tpbackend.storage.storage_v2 import (
    Activity,
    User,
)
from tpbackend.api_v2.users.query import UserStatsQuery, UserQuery
from tpbackend.api_v2.users.models import UserStatsV2, PublicUserModelV2
from tpbackend.api_v2.responses import bad_request, not_found
import logging
from typing import TypeAlias
from fastapi import APIRouter
from tpbackend.api_v2.types import (
    PATH_IDS_CSV,
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
) -> list[UserStatsV2]:
    bf = parseTS(before)
    af = parseTS(after)

    query = UserStatsQuery.base()
    if uids and len(uids) > 0:
        if len(uids) > 100:
            return bad_request("Cannot request more than 100 users at once")
        query = UserStatsQuery.apply_ids(query, uids)

    query = UserStatsQuery.apply_filters(
        query,
        before=bf,
        after=af,
        game_id=game_id,
        platform_id=platform_id,
    )

    query = UserStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, offset))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    # print("__get_users_stats QUERY", query.sql())
    return [UserStatsV2.from_user(user) for user in query]


@router.get(
    "/user-stats/{user_id}",
    tags=["users", "stats"],
    response_model=UserStatsV2,
)
def get_user_stats(
    user_id: int,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    game: int | None = None,
    platform: int | None = None,
) -> UserStatsV2:
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
    "/users-stats/{user_ids}", response_model=list[UserStatsV2], tags=["users", "stats"]
)
def get_users_stats(
    user_ids: str = PATH_IDS_CSV,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    game: int | None = None,
    platform: int | None = None,
    sort: UserStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[UserStatsV2]:
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


@router.get("/users-stats", tags=["users", "stats"], response_model=list[UserStatsV2])
def get_all_users_stats(
    offset=0,
    limit=25,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    sort: UserStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[UserStatsV2]:
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
) -> list[PublicUserModelV2]:
    query = UserQuery.base()
    if ids and len(ids) > 0:
        query = UserQuery.apply_ids(query=query, user_ids=ids)
    query = UserQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, offset))
    if limit:
        query = query.limit(clamp(limit, 1, 100))
    return [PublicUserModelV2.from_user(u) for u in query]


@router.get("/user/{user_id}", tags=["users"], response_model=PublicUserModelV2)
def get_user_by_id(user_id: int) -> PublicUserModelV2:
    x = __get_users(ids=[int(user_id)])
    if len(x) == 0:
        return not_found("User not found")
    return x[0]


@router.get("/users/{user_ids}", tags=["users"], response_model=list[PublicUserModelV2])
def get_users_by_ids(
    user_ids: str,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicUserModelV2]:
    gids = parse_csv(user_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 users at once")
    return __get_users(
        ids=gids,
        sort=sort,
        order=order,
    )


@router.get("/users", tags=["users"], response_model=list[PublicUserModelV2])
def get_all_users(
    offset=0,
    limit=25,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicUserModelV2]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_users(
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
