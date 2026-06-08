import datetime
import json
from typing import Literal, cast
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from peewee import fn
from tpbackend.api_models import (
    GameWithStats,
    PaginatedActivities,
    PaginatedGameWithStats,
    PaginatedPlatformsWithStats,
    PaginatedUserWithStats,
    PlatformWithStats,
    PublicActivityModel,
    PublicGameModel,
    PublicPlatformModel,
    PublicUserModel,
    UserWithStats,
    Totals,
)
from tpbackend.utils import (
    search_games_for_api,
)
from tpbackend.utils2 import (
    clamp,
    max_int as max,
    truncateMilliseconds,
    validateTS,
)
from tpbackend import bot
from tpbackend import steamgriddb
from tpbackend.storage.storage_v2 import (
    Activity_or_none,
    Game_or_none,
    Platform_or_none,
    Activity,
    User_or_none,
)
from tpbackend.cache import cache_set, cache_get
from tpbackend.api_responses import bad_request, not_found
import logging

logger = logging.getLogger("api_v1")

# app = FastAPI(title="Timeplayed")
router = APIRouter()
router_not_deprecated = APIRouter()

ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712

# This file is a mess because of circular imports hell

################ HELPERS ##################


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


###############
# SteamGridDB
###############

# SGDB handles caching internally


@router_not_deprecated.get(
    "/sgdb/search",
    tags=["SteamGridDB"],
    response_model=list[steamgriddb.SGDB_Game] | None,
    description="Searches SteamGridDB for games",
)
def search_sgdb(query: str) -> list[steamgriddb.SGDB_Game] | None:
    return steamgriddb.search(query)


@router_not_deprecated.get(
    "/sgdb/grids/{sgdb_game_id}",
    tags=["SteamGridDB"],
    response_model=list[steamgriddb.SGDB_Grid] | None,
    description="Gets grids for a game from SteamGridDB",
)
def sgdb_grids(sgdb_game_id: int) -> list[steamgriddb.SGDB_Grid] | None:
    return steamgriddb.get_grids(sgdb_game_id)


@router_not_deprecated.get(
    "/sgdb/grids/{sgdb_game_id}/best",
    tags=["SteamGridDB"],
    response_model=steamgriddb.SGDB_Grid | None,
    description="Tries to get the best grid for a game from SteamGridDB",
)
def best_grid_sgdb(sgdb_game_id: int) -> steamgriddb.SGDB_Grid | None:
    return steamgriddb.get_best_grid(sgdb_game_id)


@router_not_deprecated.get(
    "/discord/avatar/{discord_user_id}",
    tags=["Discord"],
    description="Returns redirect to Discord avatar URL for a given Discord user ID",
)
def redirect_discord_avatar(discord_user_id: str | int):
    def _get_url(discord_user_id: str | int) -> str:
        discord_user_id = int(discord_user_id)
        cache_key = f"get_discord_avatar_url:{discord_user_id}"
        cached = cache_get(cache_key)
        if cached:
            return cached.decode("utf-8")  # type: ignore
        url = bot.avatar_from_discord_user_id(discord_user_id)
        cache_set(cache_key, url, ex=3600)
        return url

    return RedirectResponse(_get_url(discord_user_id), status_code=307)
