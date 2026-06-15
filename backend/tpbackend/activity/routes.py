from fastapi import APIRouter, Path, Query
from typing import Literal
from tpbackend.api.params import query_id, query_ts, sorts
from tpbackend.storage import Activity
from tpbackend.activity.models import API_Activity, Total
from tpbackend.activity.query import ActivityQuery
from tpbackend.utils2 import parse_csv, clamp, validateTS, dt_to_ts
from tpbackend.api.params import AscDescOrder, path_csv, query_csv, offset, limit
from tpbackend.api.responses import bad_request, not_found
from peewee import fn
import logging

logger = logging.getLogger("activity_routes")

router = APIRouter()


def __get_newest_or_oldest(
    which: Literal["newest", "oldest"],
    user=None,
    game=None,
    platform=None,
) -> API_Activity | None:
    query = ActivityQuery.base(include_hidden=False)
    if user:
        query = ActivityQuery.user(query, user)
    if game:
        query = ActivityQuery.game(query, game)
    if platform:
        query = ActivityQuery.platform(query, platform)
    if query.count() == 0:
        return None
    query = ActivityQuery.apply_sort(
        query, "timestamp", "desc" if which == "newest" else "asc"
    )
    return API_Activity.from_activity(query.first())


@router.get("/activity/newest", tags=["activities"], response_model=API_Activity)
def get_newest_activity(
    user=query_id("user"),
    game=query_id("game"),
    platform=query_id("platform"),
) -> API_Activity | None:
    x = __get_newest_or_oldest(which="newest", user=user, game=game, platform=platform)
    if not x:
        raise not_found("No activity found")
    return x


@router.get("/activity/oldest", tags=["activities"], response_model=API_Activity)
def get_oldest_activity(
    user=query_id("user"),
    game=query_id("game"),
    platform=query_id("platform"),
) -> API_Activity | None:
    x = __get_newest_or_oldest(which="oldest", user=user, game=game, platform=platform)
    if not x:
        raise not_found("No activity found")
    return x


@router.get(
    "/activity/{id}",
    tags=["activities"],
    response_model=API_Activity,
)
def get_single_activity(id: int) -> API_Activity:
    query = ActivityQuery.base(include_hidden=False)
    query = ActivityQuery.id(query, id)
    activity = query.first()
    if not activity:
        return not_found("Activity not found")
    return API_Activity.from_activity(activity)


@router.get(
    "/activities/{ids}",
    tags=["activities"],
    response_model=list[API_Activity],
)
def get_many_activities(ids=path_csv("activity ids")) -> list[API_Activity]:
    aids = parse_csv(ids)  # haha
    if len(aids) > 100:
        return bad_request("Cannot request more than 100 activities at once")

    activities = ActivityQuery.base()
    activities = ActivityQuery.ids(activities, aids)
    return [API_Activity.from_activity(a) for a in activities]


@router.get(
    "/activities",
    tags=["activities"],
    response_model=list[API_Activity],
)
def get_activities(
    offset=offset(),
    limit=limit(),
    order: AscDescOrder = "desc",
    sort=sorts(list(ActivityQuery.SORTS.keys()), "timestamp"),
    user=query_id("user"),
    game=query_id("game"),
    platform=query_id("platform"),
    before=query_ts("before"),
    after=query_ts("after"),
) -> list[API_Activity]:
    limit = clamp(int(limit), 1, 500)
    offset = max(0, int(offset))
    before, after = validateTS(before), validateTS(after)

    query = ActivityQuery.base(include_hidden=False)
    if user is not None:
        query = ActivityQuery.user(query, user)
    if game is not None:
        query = ActivityQuery.game(query, game)
    if platform is not None:
        query = ActivityQuery.platform(query, platform)
    if before is not None:
        query = ActivityQuery.before(query, before)
    if after is not None:
        query = ActivityQuery.after(query, after)
    query = ActivityQuery.apply_sort(query, sort, order)
    query = query.offset(offset).limit(limit)
    return [API_Activity.from_activity(a) for a in query]


@router.get("/total", response_model=Total, tags=["activities"])
def get_total(
    users=query_csv("users"),
    games=query_csv("games"),
    platforms=query_csv("platforms"),
    before=query_ts("before"),
    after=query_ts("after"),
) -> Total:
    before, after = validateTS(before), validateTS(after)
    query = ActivityQuery.base(include_hidden=False)
    if users:
        query = ActivityQuery.users(query, parse_csv(users))
    if games:
        query = ActivityQuery.games(query, parse_csv(games))
    if platforms:
        query = ActivityQuery.platforms(query, parse_csv(platforms))
    if before:
        query = ActivityQuery.before(query, before)
    if after:
        query = ActivityQuery.after(query, after)
    first = None
    last = None
    logger.info(f"Total Query: {query.sql()}")
    count = query.count()
    if count > 0:
        firstq = query.select(fn.min(Activity.timestamp)).scalar()
        lastq = query.select(fn.max(Activity.timestamp)).scalar()
        if firstq:
            first = dt_to_ts(firstq)
        if lastq:
            last = dt_to_ts(lastq)
    return Total(
        seconds=query.select(fn.SUM(Activity.seconds)).scalar() or 0,
        activity_count=count,
        game_count=query.select(fn.COUNT(fn.DISTINCT(Activity.game))).scalar() or 0,
        platform_count=query.select(fn.COUNT(fn.DISTINCT(Activity.platform))).scalar()
        or 0,
        user_count=query.select(fn.COUNT(fn.DISTINCT(Activity.user))).scalar() or 0,
        first_activity=first,
        last_activity=last,
    )
