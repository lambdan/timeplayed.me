import datetime
from typing import cast
from fastapi import APIRouter
from tpbackend.activity.query import ActivityQuery
from tpbackend.api.params import query_id, query_ts
from tpbackend.charts.models import PlaytimeChart
from tpbackend.storage import (
    Activity,
)
import logging


logger = logging.getLogger("charts")
router = APIRouter()

# TODO, get rid of this file? move it somewhere else?


@router.get("/playtime/by_day", tags=["charts"], response_model=PlaytimeChart)
def get_playtime_by_day(
    user=query_id("user"),
    game=query_id("game"),
    platform=query_id("platform"),
    before=query_ts("before"),
    after=query_ts("after"),
) -> PlaytimeChart:
    query = ActivityQuery.base()

    if user:
        query = ActivityQuery.user(query, user)
    if game:
        query = ActivityQuery.game(query, game)
    if platform:
        query = ActivityQuery.platform(query, platform)
    if before:
        query = ActivityQuery.before(query, before)
    if after:
        query = ActivityQuery.after(query, after)

    daily_seconds: dict[datetime.date, int] = {}
    for activity in query:
        activity = cast(Activity, activity)
        end_time = activity.get_datetime()
        start_time = end_time - datetime.timedelta(seconds=activity.get_seconds())

        start_date = start_time.date()
        end_date = end_time.date()

        if start_date == end_date:
            daily_seconds[start_date] = (  # type: ignore
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
    return PlaytimeChart.parse_obj(data)
