from typing import Literal, cast
from tpbackend.utils2 import clamp, max_int as max, validateTS, parseTS, parse_csv
from tpbackend.storage.storage_v2 import (
    Activity,
    User,
)
from tpbackend.api_responses import bad_request
from tpbackend.api_v2.users.query import UserStatsQuery, UserQuery
from tpbackend.api_v2.users.models import UserStatsV2, PublicUserModelV2
import logging
from typing import TypeAlias

from fastapi import APIRouter, Query, Path

logger = logging.getLogger("api_v2")
router = APIRouter()

AscDescOrder: TypeAlias = Literal["asc", "desc"]


IDS_CSV = Path(
    description="Specify single ID, or multiple (separated by comma)",
    openapi_examples={
        "single": {"value": 1, "description": "Single ID"},
        "multiple": {"value": "1,2,3", "description": "Multiple IDs"},
    },
)
TS_QUERY_BEFORE = Query(
    default=None,
    description="Timestamp (in milliseconds). Only include activities before this timestamp.",
)

TS_QUERY_AFTER = Query(
    default=None,
    description="Timestamp (in milliseconds). Only include activities after this timestamp.",
)
ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712


################ HELPERS ##################


@router.get(
    "/{user_ids}/stats", response_model=list[UserStatsV2], tags=["users", "stats"]
)
def get_users_stats(
    user_ids: int | str = IDS_CSV,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    game_id: int | None = None,
    platform_id: int | None = None,
    sort: UserStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[UserStatsV2]:
    uids = parse_csv(user_ids)
    bf = parseTS(before)
    af = parseTS(after)

    if len(uids) > 100:
        return bad_request("Cannot request more than 100 users at once")

    query = UserStatsQuery.base()
    query = UserStatsQuery.apply_ids(query, uids)
    query = UserStatsQuery.apply_filters(
        query,
        before=bf,
        after=af,
        game_id=game_id,
        platform_id=platform_id,
    )
    query = UserStatsQuery.apply_sort(query, sort, order)
    return [UserStatsV2.from_user(user) for user in query]


@router.get("/stats", tags=["users", "stats"], response_model=list[UserStatsV2])
def get_all_users_stats(
    offset=0,
    limit=25,
    game_id: int | None = None,
    platform_id: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    sort: UserStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[UserStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    bf, af = parseTS(before), parseTS(after)

    query = UserStatsQuery.base()
    query = UserStatsQuery.apply_filters(
        query,
        before=bf,
        after=af,
        game_id=game_id,
        platform_id=platform_id,
    )
    query = UserStatsQuery.apply_sort(query, sort, order)
    query = query.offset(offset).limit(limit)
    return [UserStatsV2.from_user(user) for user in query]


@router.get("/{ids}", tags=["users"], response_model=list[PublicUserModelV2])
def get_users(
    ids: int | str = IDS_CSV,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicUserModelV2]:
    gids = parse_csv(ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 users at once")

    query = UserQuery.base()
    query = UserQuery.apply_ids(query, gids)
    query = UserQuery.apply_sort(query, sort, order)
    return [PublicUserModelV2.from_user(u) for u in query]


@router.get("", tags=["users"], response_model=list[PublicUserModelV2])
def get_all_users(
    offset=0,
    limit=25,
    sort: UserQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicUserModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    query = UserQuery.base()
    query = UserQuery.apply_sort(query, sort, order)
    query = query.offset(offset).limit(limit)

    query = User.select().order_by(User.id.asc()).offset(offset).limit(limit)
    return [PublicUserModelV2.from_user(u) for u in query]
