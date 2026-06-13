from fastapi import APIRouter, Path
from typing import Literal
from tpbackend.activity.models import API_Activity
from tpbackend.activity.query import ActivityQuery
from tpbackend.utils2 import parse_csv, clamp, validateTS
from tpbackend.common.types import AscDescOrder, QUERY_TS_AFTER, QUERY_TS_BEFORE
from tpbackend.api.responses import bad_request, not_found

router = APIRouter()


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
def get_many_activities(
    ids: str = Path(description="Comma-separated list of activity IDs"),
) -> list[API_Activity]:
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
    offset=0,
    limit=100,
    order: AscDescOrder = "desc",
    sort: Literal["timestamp", "id"] = "timestamp",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
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
