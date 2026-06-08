import datetime
from typing import Literal, cast
from peewee import JOIN, fn
from tpbackend.api_v2_models import (
    GameStatsV2,
    PlatformStatsV2,
    PublicActivityModelV2,
    PublicGameModelV2,
    PublicPlatformModelV2,
    PublicUserModelV2,
    UserStatsV2,
)
from tpbackend.utils import (
    search_games,
)
from tpbackend.utils2 import clamp, max_int as max, validateTS, parseTS, parse_csv
from tpbackend.storage.storage_v2 import (
    Game_or_none,
    Activity,
    Game,
    User,
)
from tpbackend.api_responses import bad_request
from tpbackend.user_query import UserQuery
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
    "/users/{user_ids}/stats", response_model=list[UserStatsV2], tags=["users", "stats"]
)
def get_users_stats(
    user_ids: int | str = IDS_CSV,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    game_id: int | None = None,
    platform_id: int | None = None,
    sort: UserQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[UserStatsV2]:
    uids = parse_csv(user_ids)
    bf = parseTS(before)
    af = parseTS(after)

    if len(uids) > 100:
        return bad_request("Cannot request more than 100 users at once")

    query = UserQuery.base().where(User.id.in_(uids))  # type: ignore
    query = UserQuery.apply_filters(
        query,
        before=bf,
        after=af,
        game_id=game_id,
        platform_id=platform_id,
    )
    query = UserQuery.apply_sort(query, sort, order)
    return [UserStatsV2.from_user(user) for user in query]


@router.get("/users/stats", tags=["users", "stats"], response_model=list[UserStatsV2])
def get_all_users_stats(
    offset=0,
    limit=25,
    game_id: int | None = None,
    platform_id: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    sort: UserQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[UserStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    bf, af = parseTS(before), parseTS(after)

    query = UserQuery.base()
    query = UserQuery.apply_filters(
        query,
        before=bf,
        after=af,
        game_id=game_id,
        platform_id=platform_id,
    )
    query = UserQuery.apply_sort(query, sort, order)
    query = query.offset(offset).limit(limit)
    return [UserStatsV2.from_user(user) for user in query]


@router.get("/users/{ids}", tags=["users"], response_model=list[PublicUserModelV2])
def get_users(ids: int | str = IDS_CSV) -> list[PublicUserModelV2]:
    gids = parse_csv(ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 users at once")

    query = User.select().where(User.id.in_(gids))  # type: ignore
    return [cast(User, u).get_api_v2_model() for u in query]


@router.get("/users", tags=["users"], response_model=list[PublicUserModelV2])
def get_all_users(
    offset=0,
    limit=25,
) -> list[PublicUserModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    query = User.select().order_by(User.id.asc()).offset(offset).limit(limit)
    return [cast(User, u).get_api_v2_model() for u in query]


#################
# Activities
#################


@router.get(
    "/activities", tags=["activities"], response_model=list[PublicActivityModelV2]
)
def get_all_activities(
    offset=0,
    limit=25,
    order: AscDescOrder = "desc",
    sort: Literal["timestamp", "id"] = "timestamp",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = TS_QUERY_BEFORE,
    after: int | None = TS_QUERY_AFTER,
    include_game_children: bool = False,
) -> list[PublicActivityModelV2]:
    limit = clamp(limit, 1, 500)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    before_dt, after_dt = None, None
    if before:
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
    if after:
        after_dt = datetime.datetime.fromtimestamp(after / 1000)

    # Build filters once
    filters = ACTIVITY_BASE_FILTERS.copy()
    if user is not None:
        filters.append(Activity.user == user)
    if game is not None:
        g = Game_or_none(game)
        if g:
            game_ids = [g.get_id()]
            if include_game_children:
                for child in g.get_children():
                    game_ids.append(child.get_id())
            filters.append(Activity.game.in_(game_ids))  # type: ignore
    if platform is not None:
        filters.append(Activity.platform == platform)

    if before_dt:
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_dt:
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    query = Activity.select().where(*filters)
    column = {
        "timestamp": Activity.timestamp,
        "id": Activity.id,
    }[sort]
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    query = query.offset(offset).limit(limit)

    data = []
    for a in query:
        data.append(cast(Activity, a).get_api_v2_model())

    return data


@router.get(
    "/activities/{activity_ids}",
    tags=["activities"],
    response_model=list[PublicActivityModelV2],
)
def get_activities(activity_ids: str | int) -> list[PublicActivityModelV2]:
    aids = parse_csv(activity_ids)  # haha
    if len(aids) > 100:
        return bad_request("Cannot request more than 100 activities at once")
    res = []
    return res


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
