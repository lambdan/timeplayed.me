import datetime
import json
from fastapi import APIRouter
from tpbackend.storage.storage_v2 import (
    Activity,
)
from tpbackend.cache import cache_set, cache_get
import logging

logger = logging.getLogger("api_v1")

router_not_deprecated = APIRouter()

ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712


##############
# For chart.js
##############


@router_not_deprecated.get("/stats/chart/playtime_by_day", tags=["charts"])
def get_playtime_by_day(
    userId: str | None = None, gameId: int | None = None, platformId: int | None = None
):
    cache_key = f"playtime_by_day:{userId}:{gameId}:{platformId}"
    cached = cache_get(cache_key)
    if cached:
        return json.loads(cached.decode("utf-8"))  # type: ignore

    query = Activity.select(Activity.timestamp, Activity.seconds)
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)
    query = query.where(*conditions)

    daily_seconds: dict[datetime.date, int] = {}
    for activity in query:
        end_time = activity.timestamp
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)
        start_time = end_time - datetime.timedelta(seconds=activity.seconds)

        start_date = start_time.date()
        end_date = end_time.date()

        if start_date == end_date:
            daily_seconds[start_date] = (
                daily_seconds.get(start_date, 0) + activity.seconds
            )
        else:
            current_date = start_date
            while current_date <= end_date:
                if current_date == start_date:
                    next_midnight = datetime.datetime.combine(
                        current_date + datetime.timedelta(days=1),
                        datetime.time.min,
                        tzinfo=datetime.timezone.utc,
                    )
                    day_seconds = round((next_midnight - start_time).total_seconds())
                elif current_date == end_date:
                    this_midnight = datetime.datetime.combine(
                        current_date,
                        datetime.time.min,
                        tzinfo=datetime.timezone.utc,
                    )
                    day_seconds = round((end_time - this_midnight).total_seconds())
                else:
                    day_seconds = 86400
                daily_seconds[current_date] = (
                    daily_seconds.get(current_date, 0) + day_seconds
                )
                current_date += datetime.timedelta(days=1)

    data = {"labels": [], "datasets": [{"label": "Playtime (seconds)", "data": []}]}
    for date in sorted(daily_seconds.keys()):
        data["labels"].append(date.strftime("%Y-%m-%d"))
        data["datasets"][0]["data"].append(daily_seconds[date])
    cache_set(cache_key, json.dumps(data))
    return data
