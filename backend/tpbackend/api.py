import datetime
import json
from typing import Literal, cast
from fastapi import FastAPI, HTTPException
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
    User,
    Game,
    Platform,
    Activity,
    User_or_none,
)
from tpbackend.cache import cache_set, cache_get
from tpbackend.api_responses import not_found
import logging

logger = logging.getLogger("api")

app = FastAPI()

ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712

# This file is a mess because of circular imports hell

################ HELPERS ##################


def get_total_playtime(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    query = Activity.select(Activity.seconds)
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_valid = truncateMilliseconds(before_valid)
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_valid = truncateMilliseconds(after_valid)
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_total_playtime:{userId}:{gameId}:{platformId}:{before_dt}:{after_dt}"
    cached = cache_get(key)
    if cached:
        return int(cached.decode("utf-8"))  # type: ignore

    query = query.where(*conditions)
    total = query.select(fn.SUM(Activity.seconds)).scalar() or 0
    cache_set(key, str(total))
    return total


def get_activity_count(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_valid = truncateMilliseconds(before_valid)
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_valid = truncateMilliseconds(after_valid)
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_activity_count:{userId}:{gameId}:{platformId}:{before_dt}:{after_dt}"
    cached = cache_get(key)
    if cached:
        return int(cached.decode("utf-8"))  # type: ignore

    r = Activity.select().where(*conditions).count()
    cache_set(key, str(r))
    return r


def get_user_count(
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_valid = truncateMilliseconds(before_valid)
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_valid = truncateMilliseconds(after_valid)
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_user_count:{before_dt}:{after_dt}:{gameId}:{platformId}"
    cached = cache_get(key)
    if cached:
        return int(cached.decode("utf-8"))  # type: ignore

    r = Activity.select(Activity.user).where(*conditions).distinct().count()
    cache_set(key, str(r))
    return r


def get_game_count(
    userId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    # iterating over Activity to only get games with activity
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)

    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_valid = truncateMilliseconds(before_valid)
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_valid = truncateMilliseconds(after_valid)
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_game_count:{userId}:{platformId}:{before_dt}:{after_dt}"
    cached = cache_get(key)
    if cached:
        return int(cached.decode("utf-8"))  # type: ignore

    r = Activity.select(Activity.game).where(*conditions).distinct().count()
    cache_set(key, str(r))
    return r


def get_platform_count(
    userId: int | None = None,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_valid = truncateMilliseconds(before_valid)
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_valid = truncateMilliseconds(after_valid)
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_platform_count:{userId}:{gameId}:{before_dt}:{after_dt}"
    cached = cache_get(key)
    if cached:
        return int(cached.decode("utf-8"))  # type: ignore

    r = Activity.select(Activity.platform).where(*conditions).distinct().count()
    cache_set(key, str(r))
    return r


def get_player_count(
    gameId: int, before: int | None = None, after: int | None = None
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    conditions.append(Activity.game == gameId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_valid = truncateMilliseconds(before_valid)
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_valid = truncateMilliseconds(after_valid)
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_player_count:{gameId}:{before_dt}:{after_dt}"
    cached = cache_get(key)
    if cached:
        return int(cached.decode("utf-8"))  # type: ignore

    r = Activity.select(Activity.user).where(*conditions).distinct().count()
    cache_set(key, str(r))
    return r


def get_oldest_or_newest_activity(
    oldest: bool,
    userid: int | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PublicActivityModel | None:
    order = "asc" if oldest else "desc"
    activities = get_activities(  # caches internally...
        offset=0,
        limit=1,
        order=order,
        user=userid,
        game=gameid,
        platform=platformid,
        before=before,
        after=after,
    )
    if len(activities.data) == 0:
        return None
    return activities.data[0]


def user_has_activities(userId: int) -> bool:
    """
    Returns True if user has any activities
    """
    return get_activities_impl(user=userId, limit=1).total > 0


def get_public_platform_by_id(platformId: int) -> PublicPlatformModel | None:
    pf = Platform_or_none(platformId)
    if not pf:
        return None
    return pf.get_api_model()


def get_public_game_by_id(gameId: int) -> PublicGameModel | None:
    g = Game_or_none(gameId)
    if not g:
        return None
    return g.get_api_model()


def get_public_user_by_id(userId: int) -> PublicUserModel | None:
    user = User_or_none(userId)
    if not user:
        return None
    return user.get_api_model()


def get_public_activity_by_id(activityId: int) -> PublicActivityModel | None:
    activity = Activity_or_none(activityId)
    if not activity:
        return None
    return activity.get_api_model()


######################## API ENDPOINTS ############################

####################
# Users
####################


@app.get("/api/users", tags=["users"], response_model=PaginatedUserWithStats)
def get_users(
    offset=0,
    limit=25,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedUserWithStats:
    """
    Get summarized users. Can also filter by gameId and platformId, and set a before/after timestamp to get a range.
    """
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)
    if before:
        before = truncateMilliseconds(before)
    if after:
        after = truncateMilliseconds(after)

    total = get_user_count(
        before=before, after=after, gameId=gameId, platformId=platformId
    )

    filters = ACTIVITY_BASE_FILTERS.copy()
    if gameId:
        filters.append(Activity.game == gameId)
    if platformId:
        filters.append(Activity.platform == platformId)
    if before:
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after:
        after_dt = datetime.datetime.fromtimestamp(after / 1000)
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_users:{offset}:{limit}:{gameId}:{platformId}:{before}:{after}"
    cached = cache_get(key)
    if cached:
        return PaginatedUserWithStats.model_validate_json(cached.decode("utf-8"))  # type: ignore

    query = Activity.select().where(*filters)
    query = query.order_by(Activity.user.asc()).distinct(Activity.user)
    activities = query[offset : offset + limit]  # type: ignore

    data = []
    for a in activities:
        userId = a.user.id
        try:
            data.append(
                get_user(
                    userId=userId,
                    gameId=gameId,
                    platformId=platformId,
                    before=before,
                    after=after,
                )
            )
        except Exception as e:
            logger.warning("Skipping user %s in get_users: %s", userId, e)
            continue
    r = PaginatedUserWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )
    cache_set(key, r.model_dump_json())
    return r


@app.get("/api/user/{userId}", tags=["users"], response_model=UserWithStats)
def get_user(
    userId: int,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
) -> UserWithStats:
    user = get_public_user_by_id(userId)
    if not user or not user_has_activities(userId):
        return not_found("User not found")

    totals = get_totals(
        userId=userId,
        gameId=gameId,
        platformId=platformId,
        before=before,
        after=after,
    )

    # activity must exist if we got this far
    first_activity = get_oldest_activity(userid=userId, gameid=gameId, platformid=platformId, before=before, after=after)  # type: ignore
    latest_activity = get_newest_activity(userid=userId, gameid=gameId, platformid=platformId, before=before, after=after)  # type: ignore
    first_activity: PublicActivityModel
    latest_activity: PublicActivityModel

    return UserWithStats(
        user=user,
        oldest_activity=first_activity,
        newest_activity=latest_activity,
        totals=totals,
    )


#################
# Activities
#################


@app.get("/api/activities", tags=["activities"], response_model=PaginatedActivities)
def get_activities(
    offset=0,
    limit=25,
    order: Literal["desc", "asc"] = "desc",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedActivities:
    # through API: use cache
    return get_activities_impl(
        use_cache=True,
        offset=offset,
        limit=limit,
        order=order,
        user=user,
        game=game,
        platform=platform,
        before=before,
        after=after,
    )


def get_activities_impl(
    offset=0,
    limit=25,
    order: Literal["desc", "asc"] = "desc",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = None,
    after: int | None = None,
    use_cache=False,
) -> PaginatedActivities:
    limit = clamp(limit, 1, 500)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)
    if before:
        before = truncateMilliseconds(before)
    if after:
        after = truncateMilliseconds(after)
    key = f"get_activities:{offset}:{limit}:{order}:{user}:{game}:{platform}:{before}:{after}"
    cached = use_cache and cache_get(key)
    if cached:
        return PaginatedActivities.model_validate_json(cached.decode("utf-8"))  # type: ignore

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
        filters.append(Activity.game == game)
    if platform is not None:
        filters.append(Activity.platform == platform)

    if before_dt:
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_dt:
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    query = Activity.select().where(*filters)
    query = (
        query.order_by(
            Activity.timestamp.desc() if order == "desc" else Activity.timestamp.asc()
        )
        .offset(offset)
        .limit(limit)
    )

    total_count = get_activity_count(
        userId=user, gameId=game, platformId=platform, before=before, after=after
    )

    data = []
    for a in query:
        data.append(a.get_api_model())

    r = PaginatedActivities(
        data=data,
        total=total_count,
        offset=offset,
        limit=limit,
        order=order,
    )

    cache_set(key, r.model_dump_json(), ex=60)
    return r


@app.get(
    "/api/activity/newest", tags=["activities"], response_model=PublicActivityModel
)
def get_newest_activity(
    userid: int | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PublicActivityModel | None:
    return get_oldest_or_newest_activity(
        oldest=False,
        userid=userid,
        gameid=gameid,
        platformid=platformid,
        before=before,
        after=after,
    )


@app.get(
    "/api/activity/oldest", tags=["activities"], response_model=PublicActivityModel
)
def get_oldest_activity(
    userid: int | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PublicActivityModel | None:
    return get_oldest_or_newest_activity(
        oldest=True,
        userid=userid,
        gameid=gameid,
        platformid=platformid,
        before=before,
        after=after,
    )


@app.get(
    "/api/activity/{activity_id}",
    tags=["activities"],
    response_model=PublicActivityModel,
)
def get_activity(activity_id: int) -> PublicActivityModel:
    activity = get_public_activity_by_id(activity_id)
    if not activity:
        return not_found("Activity not found")
    return activity


##############
# Games
#############


@app.get("/api/games", tags=["games"], response_model=PaginatedGameWithStats)
def get_games(
    offset=0,
    limit=25,
    userId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedGameWithStats:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    filters = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        filters.append(Activity.user == userId)
    if platformId:
        filters.append(Activity.platform == platformId)
    if before:
        before = truncateMilliseconds(before)
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after:
        after = truncateMilliseconds(after)
        after_dt = datetime.datetime.fromtimestamp(after / 1000)
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_games:{offset}:{limit}:{userId}:{platformId}:{before}:{after}"
    cached = cache_get(key)
    if cached:
        return PaginatedGameWithStats.model_validate_json(cached.decode("utf-8"))  # type: ignore

    query = Activity.select().where(*filters)
    query = query.order_by(Activity.game.asc()).distinct(Activity.game)
    activities = query[offset : offset + limit]  # type: ignore

    total = get_game_count(
        userId=userId, platformId=platformId, before=before, after=after
    )

    data = []
    for a in activities:
        gameId = int(a.game.id)
        try:
            data.append(
                get_game(
                    userId=userId,
                    gameId=gameId,
                    platformId=platformId,
                    before=before,
                    after=after,
                )
            )
        except Exception as e:
            logger.warning("Skipping game %s in get_games: %s", gameId, e)
            continue
    r = PaginatedGameWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )
    cache_set(key, r.model_dump_json())
    return r


@app.get("/api/game/{gameId}", tags=["games"], response_model=GameWithStats)
def get_game(
    gameId: int,
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    platformId: int | None = None,
) -> GameWithStats:
    game = Game_or_none(gameId)
    if not game:
        return not_found("Game not found")

    key = f"game_with_stats:{gameId}:{userId}:{before}:{after}:{platformId}"
    cached = cache_get(key)
    if cached:
        return GameWithStats.model_validate_json(cached.decode("utf-8"))  # type: ignore

    gameModel = game.get_api_model()

    totals = get_totals(
        userId=userId,
        gameId=game.get_id(),
        before=before,
        after=after,
        platformId=platformId,
    )

    total_playtime_all_games = get_total_playtime(
        userId=userId, before=before, after=after, platformId=platformId
    )
    total_playtime_this_game = get_total_playtime(
        userId=userId,
        gameId=game.get_id(),
        before=before,
        after=after,
        platformId=platformId,
    )
    percent = 0
    if total_playtime_all_games > 0:
        percent = total_playtime_this_game / total_playtime_all_games

    r = GameWithStats(
        game=gameModel,
        totals=totals,
        percent=percent,
        oldest_activity=get_oldest_activity(
            userid=userId,
            gameid=game.get_id(),
            before=before,
            after=after,
            platformid=platformId,
        ),
        newest_activity=get_newest_activity(
            userid=userId,
            gameid=game.get_id(),
            before=before,
            after=after,
            platformid=platformId,
        ),
    )

    cache_set(key, r.model_dump_json())
    return r


##############
# Platforms
##############


@app.get(
    "/api/platforms", tags=["platforms"], response_model=PaginatedPlatformsWithStats
)
def get_platforms(
    offset=0,
    limit=25,
    userId: int | None = None,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedPlatformsWithStats:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    filters = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        filters.append(Activity.user == userId)
    if gameId:
        filters.append(Activity.game == gameId)
    if before:
        before = truncateMilliseconds(before)
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after:
        after = truncateMilliseconds(after)
        after_dt = datetime.datetime.fromtimestamp(after / 1000)
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    key = f"get_platforms:{offset}:{limit}:{userId}:{gameId}:{before}:{after}"
    cached = cache_get(key)
    if cached:
        return PaginatedPlatformsWithStats.model_validate_json(cached.decode("utf-8"))  # type: ignore

    query = Activity.select().where(*filters)
    query = query.order_by(Activity.platform.asc()).distinct(Activity.platform)
    activities = query[offset : offset + limit]  # type: ignore

    total = get_platform_count(userId=userId, gameId=gameId, before=before, after=after)

    data = []
    for a in activities:
        platformId = int(a.platform.id)
        try:
            data.append(
                get_platform(
                    userId=userId,
                    gameId=gameId,
                    platformId=platformId,
                    before=before,
                    after=after,
                )
            )
        except Exception as e:
            logger.warning("Skipping platform %s in get_platforms: %s", platformId, e)
            continue
    r = PaginatedPlatformsWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )
    cache_set(key, r.model_dump_json())
    return r


@app.get(
    "/api/platform/{platformId}", tags=["platforms"], response_model=PlatformWithStats
)
def get_platform(
    platformId: int,
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
) -> PlatformWithStats:
    platformModel = get_public_platform_by_id(platformId)
    if not platformModel:
        return not_found("Platform not found")

    totals = get_totals(
        userId=userId, gameId=gameId, before=before, after=after, platformId=platformId
    )

    total_playtime_all_pfs = get_total_playtime(
        userId=userId, before=before, after=after, gameId=gameId
    )
    total_playtime_this_pf = get_total_playtime(
        userId=userId, gameId=gameId, before=before, after=after, platformId=platformId
    )
    percent = 0
    if total_playtime_all_pfs > 0:
        percent = total_playtime_this_pf / total_playtime_all_pfs

    r = PlatformWithStats(
        platform=platformModel,
        totals=totals,
        percent=percent,
        oldest_activity=get_oldest_activity(
            userid=userId,
            gameid=gameId,
            before=before,
            after=after,
            platformid=platformId,
        ),
        newest_activity=get_newest_activity(
            userid=userId,
            gameid=gameId,
            before=before,
            after=after,
            platformid=platformId,
        ),
    )

    return r


#################
# Totals
#################


@app.get("/api/totals", tags=["totals"], response_model=Totals)
def get_totals(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> Totals:

    return Totals(
        playtime_secs=get_total_playtime(
            before=before,
            after=after,
            userId=userId,
            gameId=gameId,
            platformId=platformId,
        ),
        activity_count=get_activity_count(
            before=before,
            after=after,
            userId=userId,
            gameId=gameId,
            platformId=platformId,
        ),
        user_count=get_user_count(
            before=before, after=after, gameId=gameId, platformId=platformId
        ),
        game_count=get_game_count(
            before=before, after=after, userId=userId, platformId=platformId
        ),
        platform_count=get_platform_count(
            before=before, after=after, userId=userId, gameId=gameId
        ),
    )


##############
# For chart.js
##############


@app.get("/api/stats/chart/playtime_by_day", tags=["charts"])
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


@app.get(
    "/api/sgdb/search",
    tags=["SteamGridDB"],
    response_model=list[steamgriddb.SGDB_Game] | None,
    description="Searches SteamGridDB for games",
)
def search_sgdb(query: str) -> list[steamgriddb.SGDB_Game] | None:
    return steamgriddb.search(query)


@app.get(
    "/api/sgdb/grids/{sgdb_game_id}",
    tags=["SteamGridDB"],
    response_model=list[steamgriddb.SGDB_Grid] | None,
    description="Gets grids for a game from SteamGridDB",
)
def sgdb_grids(sgdb_game_id: int) -> list[steamgriddb.SGDB_Grid] | None:
    return steamgriddb.get_grids(sgdb_game_id)


@app.get(
    "/api/sgdb/grids/{sgdb_game_id}/best",
    tags=["SteamGridDB"],
    response_model=steamgriddb.SGDB_Grid | None,
    description="Tries to get the best grid for a game from SteamGridDB",
)
def best_grid_sgdb(sgdb_game_id: int) -> steamgriddb.SGDB_Grid | None:
    return steamgriddb.get_best_grid(sgdb_game_id)


@app.get(
    "/api/discord/avatar/{discord_user_id}",
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
