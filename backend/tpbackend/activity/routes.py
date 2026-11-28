from fastapi import APIRouter
from typing import Literal
from tpbackend.activity.controller import (
    abort_live_activity_through_api,
    add_through_api,
    delete_through_api,
    get_live_activity_through_api,
    patch_through_api,
    start_live_activity_through_api,
    stop_live_activity_through_api,
)

from tpbackend.api.auth import AuthenticatedUser, ManualActivityUser, OptionalUser
from tpbackend.api.params import (
    query_game_include_children,
    query_id,
    query_platform_include_children,
    query_ts,
    sorts,
)
from tpbackend.storage import Activity, User
from tpbackend.user.utils import check_user_filter
from tpbackend.activity.models import (
    API_Activity,
    API_LiveActivity,
    API_Playing,
    API_PostActivity,
    API_PostLiveActivity,
    API_PatchActivity,
    Total,
)
from tpbackend.activity.query import ActivityQuery
from tpbackend.activity.playing import playing_now
from tpbackend.utils2 import parse_csv, clamp, validateTS, dt_to_ts, now
from tpbackend.api.params import AscDescOrder, path_csv, query_csv, offset, limit
from tpbackend.api.responses import bad_request, not_found
from peewee import fn
import logging

logger = logging.getLogger("activity_routes")

router = APIRouter()


def __get_newest_or_oldest(
    which: Literal["newest", "oldest"],
    viewer: User | None,
    user=None,
    game=None,
    platform=None,
    include_children=False,
    include_child_platforms=False,
) -> API_Activity | None:
    # 404 for private users, but to themselves
    check_user_filter(user, viewer)
    query = ActivityQuery.base()
    if user:
        query = ActivityQuery.user(query, user)
    else:
        query = ActivityQuery.visible_to(query)
    if game:
        query = ActivityQuery.game(query, game, include_children)
    if platform:
        query = ActivityQuery.platform(query, platform, include_child_platforms)
    if query.count() == 0:
        return None
    order = "desc" if which == "newest" else "asc"
    query = ActivityQuery.apply_sort(query, "timestamp", order)
    return API_Activity.from_activity(query.first())


@router.post(
    "/activity",
    tags=["activities", "authenticated"],
    response_model=API_Activity,
)
def add_activity(user: ManualActivityUser, data: API_PostActivity) -> API_Activity:
    return add_through_api(user=user, data=data)


@router.get("/activity/newest", tags=["activities"], response_model=API_Activity)
def get_newest_activity(
    viewer: OptionalUser,
    user=query_id("user"),
    game=query_id("game"),
    include_children: bool = query_game_include_children(),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
) -> API_Activity | None:
    x = __get_newest_or_oldest(
        which="newest",
        viewer=viewer,
        user=user,
        game=game,
        platform=platform,
        include_children=include_children,
        include_child_platforms=include_child_platforms,
    )
    if not x:
        raise not_found("No activity found")
    return x


@router.get("/activity/oldest", tags=["activities"], response_model=API_Activity)
def get_oldest_activity(
    viewer: OptionalUser,
    user=query_id("user"),
    game=query_id("game"),
    include_children: bool = query_game_include_children(),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
) -> API_Activity | None:
    x = __get_newest_or_oldest(
        which="oldest",
        viewer=viewer,
        user=user,
        game=game,
        platform=platform,
        include_children=include_children,
        include_child_platforms=include_child_platforms,
    )
    if not x:
        raise not_found("No activity found")
    return x


@router.get("/playing", tags=["activities", "live"], response_model=list[API_Playing])
def get_playing() -> list[API_Playing]:
    """
    Everyone playing something right now, from manual tracking and Discord, newest first.
    The same user, game and platform from both is listed once, with the earliest start
    """
    return playing_now(now())


@router.get(
    "/activity/live",
    tags=["activities", "live", "authenticated"],
    response_model=API_LiveActivity,
)
def get_live_activity(user: ManualActivityUser) -> API_LiveActivity:
    return get_live_activity_through_api(user=user)


@router.post(
    "/activity/live",
    tags=["activities", "authenticated", "live"],
    response_model=API_LiveActivity,
)
def start_live_activity(
    user: ManualActivityUser, data: API_PostLiveActivity
) -> API_LiveActivity:
    return start_live_activity_through_api(user=user, data=data)


@router.post(
    "/activity/live/stop",
    tags=["activities", "authenticated", "live"],
)
def stop_live_activity(user: ManualActivityUser) -> API_Activity:
    return stop_live_activity_through_api(user=user)


@router.delete("/activity/live", tags=["activities", "authenticated", "live"])
def abort_live_activity(user: ManualActivityUser):
    return abort_live_activity_through_api(user=user)


@router.get(
    "/activity/{id}",
    tags=["activities"],
    response_model=API_Activity,
)
def get_single_activity(viewer: OptionalUser, id: int) -> API_Activity:
    query = ActivityQuery.visible_to(ActivityQuery.base(), viewer)
    query = ActivityQuery.id(query, id)
    activity = query.first()
    if not activity:
        return not_found("Activity not found")
    return API_Activity.from_activity(activity)


@router.delete("/activity/{id}", tags=["activities", "authenticated"])
def delete_activity(id: int, user: AuthenticatedUser):
    # no permission needed, deleting can't inflate anything
    return delete_through_api(user=user, activity_id=id)


@router.patch(
    "/activity/{id}",
    tags=["activities", "authenticated"],
    response_model=API_Activity,
)
def patch_activity(
    id: int, data: API_PatchActivity, user: ManualActivityUser
) -> API_Activity:
    """Change the game and/or platform of one of your own activities, like an emulator to the actual game. Only the fields that are sent are changed"""
    return patch_through_api(user=user, activity_id=id, data=data)


@router.get(
    "/activities/{ids}",
    tags=["activities"],
    response_model=list[API_Activity],
)
def get_many_activities(
    viewer: OptionalUser, ids=path_csv("activity ids")
) -> list[API_Activity]:
    aids = parse_csv(ids)  # haha
    if len(aids) > 100:
        return bad_request("Cannot request more than 100 activities at once")

    activities = ActivityQuery.visible_to(ActivityQuery.base(), viewer)
    activities = ActivityQuery.ids(activities, aids)
    return [API_Activity.from_activity(a) for a in activities]


@router.get(
    "/activities",
    tags=["activities"],
    response_model=list[API_Activity],
)
def get_activities(
    viewer: OptionalUser,
    offset=offset(),
    limit=limit(),
    order: AscDescOrder = "desc",
    sort=sorts(list(ActivityQuery.SORTS.keys()), "timestamp"),
    user=query_id("user"),
    game=query_id("game"),
    include_children: bool = query_game_include_children(),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
    before=query_ts("before"),
    after=query_ts("after"),
) -> list[API_Activity]:
    limit = clamp(int(limit), 1, 500)
    offset = max(0, int(offset))
    before, after = validateTS(before), validateTS(after)
    # 404 for private users, but to themselves
    check_user_filter(user, viewer)

    query = ActivityQuery.base()
    if user is not None:
        query = ActivityQuery.user(query, user)
    else:
        query = ActivityQuery.visible_to(query)
    if game is not None:
        query = ActivityQuery.game(query, game, include_children)
    if platform is not None:
        query = ActivityQuery.platform(query, platform, include_child_platforms)
    if before is not None:
        query = ActivityQuery.before(query, before)
    if after is not None:
        query = ActivityQuery.after(query, after)
    query = ActivityQuery.apply_sort(query, sort, order)
    query = query.offset(offset).limit(limit)
    return [API_Activity.from_activity(a) for a in query]


@router.get("/total", response_model=Total, tags=["activities"])
def get_total(
    viewer: OptionalUser,
    users=query_csv("users"),
    games=query_csv("games"),
    platforms=query_csv("platforms"),
    before=query_ts("before"),
    after=query_ts("after"),
) -> Total:
    before, after = validateTS(before), validateTS(after)
    query = ActivityQuery.base(include_hidden=False)
    if users:
        # 404 for private users, but to themselves
        check_user_filter(parse_csv(users), viewer)
        query = ActivityQuery.users(query, parse_csv(users))
    else:
        query = ActivityQuery.visible_to(query)
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
    # logger.info(f"Total Query: {query.sql()}")
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
