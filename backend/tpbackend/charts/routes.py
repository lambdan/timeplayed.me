import datetime
from fastapi import APIRouter
from tpbackend.common.types import QUERY_TS_BEFORE, QUERY_TS_AFTER
from tpbackend.storage import (
    Activity,
)
import logging

logger = logging.getLogger("charts")
router = APIRouter()
ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712

# TODO, get rid of this file? move it somewhere else?


@router.get("/playtime/by_day", tags=["charts"])
def get_playtime_by_day(
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
):
    query = Activity.select(Activity.timestamp, Activity.seconds)
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if user:
        conditions.append(Activity.user == user)
    if game:
        conditions.append(Activity.game == game)
    if platform:
        conditions.append(Activity.platform == platform)
    if before:
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after:
        after_dt = datetime.datetime.fromtimestamp(after / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore
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
    return data
