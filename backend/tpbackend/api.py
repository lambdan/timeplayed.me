import datetime
import os
from typing import Literal
from fastapi import FastAPI, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn
from tpbackend.api_models import (
    GameStatsResponse,
    GameWithStats,
    PaginatedActivities,
    PaginatedGameWithStats,
    PaginatedGames,
    PaginatedPlatforms,
    PaginatedUsers,
    PlatformWithStats,
    PublicActivityModel,
    PublicGameModel,
    PublicPlatformModel,
    PublicUserModel,
    SummarizedUserResponse,
    TotalsResponse,
)
from tpbackend.utils import clamp, max_int as max, today, thisHour, validateTS
from tpbackend import bot
from tpbackend import steamgriddb
from tpbackend.storage.storage_v2 import LiveActivity, User, Game, Platform, Activity
import logging

################
# Models
################


logger = logging.getLogger("api")

app = FastAPI()

CACHE = {}
CACHE_MAX = int(os.environ.get("CACHE_MAX", 1000))
CACHE_FLUSHES = 0


def cacheGet(key: str):
    """
    Gets value from cache. Returns None if not found.
    """
    if key in CACHE:
        logger.info("Cache hit: %s", key)
        return CACHE[key]
    return None


def cacheSetReturn(key: str, value):
    """
    Sets value in cache. Flushes if size exceeded. Returns same value.
    """
    if len(CACHE) > CACHE_MAX:
        global CACHE_FLUSHES
        CACHE_FLUSHES += 1
        logger.info(
            "Cache size exceeded, flushing for the %s'th time 🚽", CACHE_FLUSHES
        )
        CACHE.clear()
    CACHE[key] = value
    return value


def fixDatetime(data):
    """
    Recursively converts datetime objects in a dictionary to milliseconds since epoch
    """
    if isinstance(data, datetime.datetime):
        if data.tzinfo is None:
            data = data.replace(tzinfo=datetime.timezone.utc)
        return int(data.timestamp() * 1000)

    if not isinstance(data, (dict, list)):
        return data

    if isinstance(data, dict):
        return {k: fixDatetime(v) for k, v in data.items()}

    if isinstance(data, list):
        return [fixDatetime(item) for item in data]


def get_public_user(userId: int | str) -> PublicUserModel | None:
    user = User.get_or_none(User.id == str(userId))
    if not user:
        return None
    return PublicUserModel(
        id=str(user.id),
        name=user.name,
        default_platform=PublicPlatformModel(
            id=user.default_platform.id,
            abbreviation=user.default_platform.abbreviation,
            name=user.default_platform.name,
        ),
    )


def get_public_activity(a: Activity | int) -> PublicActivityModel:
    if isinstance(a, int):
        a = Activity.get_or_none(Activity.id == a)  # type: ignore
        if not a:
            raise HTTPException(status_code=404, detail="Activity not found")

    activity: Activity = a  # type: ignore
    return PublicActivityModel(
        id=activity.id,  # type: ignore
        timestamp=tsFromActivity(activity),
        user=get_public_user(activity.user.id),  # type: ignore
        game=PublicGameModel(
            id=activity.game.id,
            name=activity.game.name,
            steam_id=activity.game.steam_id,
            sgdb_id=activity.game.sgdb_id,
            image_url=activity.game.image_url,
            aliases=activity.game.aliases,
            release_year=activity.game.release_year,
        ),
        platform=PublicPlatformModel(
            id=activity.platform.id,
            abbreviation=activity.platform.abbreviation,
            name=activity.platform.name,
        ),
        seconds=activity.seconds,  # type: ignore
    )


def tsFromActivity(activity: Activity) -> int:
    dt = activity.timestamp
    if isinstance(dt, int):
        return dt
    if dt.tzinfo is None:  # type: ignore
        dt = dt.replace(tzinfo=datetime.timezone.utc)  # type: ignore
    return int(dt.timestamp() * 1000)  # type: ignore


####################
# Users
####################


@app.get("/api/users/{userId}/has_activities", tags=["users"])
def user_has_activities(userId: int | str) -> bool:
    """
    Returns True if user has any activities
    """
    any_activity = Activity.select().where(Activity.user == str(userId)).first()
    return any_activity != None


@app.get("/api/users/{userId}", tags=["users"], response_model=SummarizedUserResponse)
def get_user(
    userId: int,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
) -> SummarizedUserResponse:
    user = get_public_user(userId)
    if not user or not user_has_activities(userId):
        raise HTTPException(status_code=404, detail="User not found")

    total_activities = get_activity_count(
        userId=userId, before=before, after=after, gameId=gameId
    )
    total_playtime = get_total_playtime(
        userId=userId, before=before, after=after, gameId=gameId
    )

    if before or after:
        return SummarizedUserResponse(
            user=user,
            total_activities=total_activities,
            total_playtime=total_playtime,
        )
    else:
        return SummarizedUserResponse(
            user=user,
            last_played=tsFromActivity(get_last_activity(userid=userId, gameid=gameId)),  # type: ignore
            total_activities=total_activities,
            total_playtime=total_playtime,
        )


@app.get("/api/users", tags=["users", "games"], response_model=PaginatedUsers)
def get_users(
    offset=0,
    limit=25,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedUsers:
    """
    Get summarized users. If gameId is provided, you get user summaries for that game.
    """
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    total = 0
    if gameId:
        total = get_player_count(gameId, before=before, after=after)
    else:
        total = get_user_count(before=before, after=after)

    filters = []
    if gameId:
        filters.append(Activity.game == gameId)
    if before:
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after:
        after_dt = datetime.datetime.fromtimestamp(after / 1000)
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    query = Activity.select()
    if len(filters) > 0:
        query = query.where(*filters)
    query = query.order_by(Activity.user.asc()).distinct(Activity.user)
    activities = query[offset : offset + limit]  # type: ignore

    data = []
    for a in activities:
        userId = int(a.user.id)
        try:
            data.append(
                get_user(userId=userId, gameId=gameId, before=before, after=after)
            )
        except Exception as e:
            logger.warning("Skipping user %s in get_users: %s", userId, e)
            continue
    return PaginatedUsers(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )


@app.get(
    "/api/users/{userId}/games", tags=["users", "games"], response_model=PaginatedGames
)
def get_user_games(userId: int, offset=0, limit=25) -> PaginatedGames:
    offset = max(0, offset)
    limit = clamp(limit, 1, 100)
    user = get_public_user(userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = (
        Activity.select(Activity.game)
        .where(Activity.user == userId)
        .distinct()
        .order_by(Activity.game.asc())
    )
    games = games[offset : offset + limit]  # type: ignore
    response = []
    for game in games:
        game_data = get_game(gameId=game.game.id, userId=userId)
        response.append(game_data)

    pr = PaginatedGames(
        data=response,
        total=get_game_count(userId=userId),
        offset=offset,
        limit=limit,
    )
    return fixDatetime(pr)  # type: ignore


@app.get("/api/users/{userId}/platforms", tags=["users", "platforms"])
def get_user_platforms(userId: int):
    user = get_public_user(userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    platforms = []
    for platform in Platform.select():
        total_playtime = get_total_playtime(userId=userId, platformId=platform.id)
        if total_playtime > 0:
            platforms.append(
                {
                    "platform": model_to_dict(platform),  # type: ignore
                    "total_playtime": total_playtime,
                    "last_played": get_last_activity(userid=userId, platformid=platform.id).timestamp,  # type: ignore
                    "total_sessions": get_activity_count(
                        userId=userId, platformId=platform.id
                    ),
                    "percent": (
                        total_playtime / get_total_playtime(userId=userId)
                        if get_total_playtime(userId=userId) > 0
                        else 0
                    ),
                }
            )
    return fixDatetime(platforms)


@app.get("/api/users/{user_id}/stats", tags=["users"])
def get_user_stats(user_id: int):
    user = User.get_or_none(User.id == user_id)  # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    oldest_activity = (
        Activity.select()
        .where(Activity.user == user)
        .order_by(Activity.timestamp.asc())
        .first()
    )
    newest_activity = (
        Activity.select()
        .where(Activity.user == user)
        .order_by(Activity.timestamp.desc())
        .first()
    )
    total_playtime = get_total_playtime(userId=user_id)
    total_activities = get_activity_count(userId=user_id)
    total_games = get_game_count(userId=user_id)
    total_platforms = get_platform_count(userId=user_id)

    oldest_activity = get_public_activity(oldest_activity) if oldest_activity else None
    newest_activity = get_public_activity(newest_activity) if newest_activity else None

    return fixDatetime(
        {
            "total": {
                "seconds": total_playtime,
                "activities": total_activities,
                "games": total_games,
                "platforms": total_platforms,
            },
            "oldest_activity": oldest_activity,
            "newest_activity": newest_activity,
            "active_days": Activity.select(
                fn.COUNT(fn.DISTINCT(fn.DATE(Activity.timestamp)))
            )
            .where(Activity.user == user)
            .scalar(),
            "average": {
                "seconds_per_game": (
                    total_playtime / total_games if total_games > 0 else 0
                ),
                "sessions_per_game": (
                    total_activities / total_games
                    if (total_activities > 0 and total_games > 0)
                    else 0
                ),
                "session_length": (
                    total_playtime / total_activities
                    if (total_activities > 0 and total_playtime > 0)
                    else 0
                ),
            },
        }
    )


#################
# Activities
#################


@app.get("/api/activities", tags=["activities"], response_model=PaginatedActivities)
def list_activities(
    offset=0,
    limit=25,
    order: Literal["desc", "asc"] = "desc",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedActivities:
    limit = clamp(limit, 1, 500)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)
    # use activity count in cache_key to invalidate cache when new activities are added/removed
    activity_count = get_activity_count(userId=user, gameId=game, platformId=platform)
    cache_key = f"activities:{offset}:{limit}:{order}:{user}:{game}:{platform}:{before}:{after}:{activity_count}"
    logger.debug("Cache key: %s", cache_key)
    cached = cacheGet(cache_key)
    if cached:
        return cached

    before_dt, after_dt = None, None
    if before:
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
    if after:
        after_dt = datetime.datetime.fromtimestamp(after / 1000)

    # Build filters once
    filters = []
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

    query = Activity.select()
    if filters:
        query = query.where(*filters)
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

    r = PaginatedActivities(
        data=[get_public_activity(activity) for activity in query],
        total=total_count,
        offset=offset,
        limit=limit,
        order=order,
    )

    return cacheSetReturn(cache_key, r)


@app.get(
    "/api/activities/last", tags=["activities"], response_model=PublicActivityModel
)
def get_last_activity(
    userid: int | None = None, gameid: int | None = None, platformid: int | None = None
) -> PublicActivityModel | None:
    """
    Returns the last activity for a user, game or platform.
    If no parameters are given, returns the last activity overall.
    """
    query = Activity.select().order_by(Activity.timestamp.desc())

    if userid:
        query = query.where(Activity.user == userid)
    if gameid:
        query = query.where(Activity.game == gameid)
    if platformid:
        query = query.where(Activity.platform == platformid)

    last_activity = query.first()

    if not last_activity:
        return None

    p = PublicActivityModel(
        id=last_activity.id,
        timestamp=tsFromActivity(last_activity),
        user=get_public_user(last_activity.user.id),  # type: ignore
        game=PublicGameModel(
            id=last_activity.game.id,
            name=last_activity.game.name,
            steam_id=last_activity.game.steam_id,
            sgdb_id=last_activity.game.sgdb_id,
            image_url=last_activity.game.image_url,
            aliases=last_activity.game.aliases,
            release_year=last_activity.game.release_year,
        ),
        platform=PublicPlatformModel(
            id=last_activity.platform.id,
            abbreviation=last_activity.platform.abbreviation,
            name=last_activity.platform.name,
        ),
        seconds=last_activity.seconds,
    )
    return p


@app.get("/api/activities/live", tags=["activities"])
def get_live_activities():
    live_activities = LiveActivity.select()
    return fixDatetime([get_public_activity(activity) for activity in live_activities])


@app.get("/api/activities/{activity_id}", tags=["activities"])
def get_activity(activity_id: int):
    activity = Activity.get_or_none(Activity.id == activity_id)  # type: ignore
    return fixDatetime(model_to_dict(activity)) if activity else {"error": "Not found"}


##############
# Games
#############


@app.get("/api/games", tags=["games"], response_model=PaginatedGameWithStats)
def get_games(limit=25, offset=0):
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = Activity.select(Activity.game).distinct()
    games = games[offset : offset + limit]  # type: ignore
    response = []
    for game in games:
        game_data = get_game(gameId=game.game.id)
        response.append(game_data)

    return PaginatedGameWithStats(
        data=response,
        total=get_game_count(),
        offset=offset,
        limit=limit,
    )


@app.get("/api/games/{gameId}", tags=["games"], response_model=GameWithStats)
def get_game(gameId: int, userId: int | None = None):
    game = Game.get_or_none(Game.id == gameId)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    r = GameWithStats(
        game=model_to_dict(game),  # type: ignore
        total_playtime=get_total_playtime(userId=userId, gameId=game.id),
        last_played=get_last_activity(
            userid=userId, gameid=game.id
        ).timestamp,  #   type: ignore
        total_sessions=get_activity_count(userId=userId, gameId=game.id),
    )

    return fixDatetime(r)


def get_player_count(
    gameId: int, before: int | None = None, after: int | None = None
) -> int:
    conditions = [Activity.game == gameId]

    before_valid, after_valid = validateTS(before), validateTS(after)
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    return Activity.select(Activity.user).where(*conditions).distinct().count()


@app.get("/api/games/{game_id}/stats", tags=["games"], response_model=GameStatsResponse)
def get_game_stats(game_id: int) -> GameStatsResponse:
    game = Game.get_or_none(Game.id == game_id)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    oldest_activity = (
        Activity.select()
        .where(Activity.game == game)
        .order_by(Activity.timestamp.asc())
        .first()
    )
    newest_activity = (
        Activity.select()
        .where(Activity.game == game)
        .order_by(Activity.timestamp.desc())
        .first()
    )
    total_playtime = get_total_playtime(gameId=game.id)
    activity_count = get_activity_count(gameId=game.id)
    platform_count = get_platform_count(gameId=game.id)
    player_count = get_player_count(gameId=game.id)

    return GameStatsResponse(
        total_playtime=total_playtime,
        activity_count=activity_count,
        platform_count=platform_count,
        player_count=player_count,
        oldest_activity=(
            get_public_activity(oldest_activity) if oldest_activity else None
        ),
        newest_activity=(
            get_public_activity(newest_activity) if newest_activity else None
        ),
    )


@app.get("/api/games/{gameId}/platforms", tags=["games", "platforms"])
def get_game_platforms(gameId: int):
    game = Game.get_or_none(Game.id == gameId)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    platforms = []
    for platform in Platform.select():
        total_playtime = get_total_playtime(gameId=game.id, platformId=platform.id)
        if total_playtime > 0:
            platforms.append(
                {
                    "platform": model_to_dict(platform),  # type: ignore
                    "total_playtime": total_playtime,
                    "last_played": get_last_activity(gameid=game.id, platformid=platform.id)["timestamp"],  # type: ignore
                    "total_sessions": get_activity_count(
                        gameId=game.id, platformId=platform.id
                    ),
                    "percent": (
                        total_playtime / get_total_playtime(gameId=game.id)
                        if get_total_playtime(gameId=game.id) > 0
                        else 0
                    ),
                }
            )
    return fixDatetime(platforms)


##############
# Platforms
##############
@app.get(
    "/api/platforms/{platform_id}", tags=["platforms"], response_model=PlatformWithStats
)
def get_platform(platform_id: int) -> PlatformWithStats:
    platform = Platform.get_or_none(Platform.id == platform_id)  # type: ignore
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    total_playtime_all_platforms = get_total_playtime()
    playtime_this_platform = (
        Activity.select(fn.SUM(Activity.seconds))
        .where(Activity.platform == platform)
        .scalar()
        or 0
    )

    data = PlatformWithStats(
        platform=model_to_dict(platform),  # type: ignore
        last_played=Activity.select(fn.MAX(Activity.timestamp))
        .where(Activity.platform == platform)
        .scalar()
        or None,
        total_sessions=Activity.select().where(Activity.platform == platform).count(),
        total_playtime=playtime_this_platform,
        percent=playtime_this_platform / total_playtime_all_platforms,
    )

    return fixDatetime(data)  # type: ignore


@app.get("/api/platforms", tags=["platforms"], response_model=PaginatedPlatforms)
def list_platforms(offset=0, limit=25) -> PaginatedPlatforms:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    platforms = Platform.select().limit(limit).offset(offset)

    r = PaginatedPlatforms(
        data=[],
        total=Platform.select().count(),
        offset=offset,
        limit=limit,
    )

    for platform in platforms:
        r.data.append(get_platform(platform.id))
    return fixDatetime(r)  # type: ignore


#################
# Totals
#################


@app.get("/api/stats", tags=["totals"], response_model=TotalsResponse)
def get_stats(before: int | None = None, after: int | None = None) -> TotalsResponse:
    return TotalsResponse(
        total_playtime=get_total_playtime(before=before, after=after),
        activities=get_activity_count(before=before, after=after),
        users=get_user_count(before=before, after=after),
        games=get_game_count(before=before, after=after),
        platforms=get_platform_count(before=before, after=after),
    )


@app.get("/api/stats/total_playtime", tags=["totals"])
def get_total_playtime(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    query = Activity.select(Activity.seconds)
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    if len(conditions) > 0:
        query = query.where(*conditions)
    total = query.select(fn.SUM(Activity.seconds)).scalar() or 0
    return total


@app.get("/api/stats/total_activities", tags=["totals"])
def get_activity_count(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    if len(conditions) > 0:
        return Activity.select().where(*conditions).count()
    return Activity.select().count()


@app.get("/api/stats/total_users", tags=["totals"])
def get_user_count(before: int | None = None, after: int | None = None) -> int:
    total = 0
    for user in User.select():
        if get_activity_count(userId=user.id, before=before, after=after) > 0:
            total += 1
    return total


@app.get("/api/stats/total_games", tags=["totals"])
def get_game_count(
    userId: int | None = None, before: int | None = None, after: int | None = None
) -> int:
    # iterating over Activity to only get games with activity
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    if len(conditions) > 0:
        return Activity.select(Activity.game).where(*conditions).distinct().count()
    return Activity.select(Activity.game).distinct().count()


@app.get("/api/stats/total_platforms", tags=["totals"])
def get_platform_count(
    userId: int | None = None,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    if len(conditions) > 0:
        return Activity.select(Activity.platform).where(*conditions).distinct().count()
    return Activity.select(Activity.platform).distinct().count()


##############
# For chart.js
##############


@app.get("/api/stats/chart/playtime_by_day", tags=["charts"])
def get_playtime_by_day(
    userId: int | None = None, gameId: int | None = None, platformId: int | None = None
):
    query = Activity.select(
        fn.DATE(Activity.timestamp).alias("date"),
        fn.SUM(Activity.seconds).alias("total_seconds"),
    ).group_by(fn.DATE(Activity.timestamp))
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)
    if conditions:
        query = query.where(*conditions)
    results = query.order_by(fn.DATE(Activity.timestamp)).tuples()
    data = {"labels": [], "datasets": [{"label": "Playtime (seconds)", "data": []}]}
    for date, total_seconds in results:
        data["labels"].append(date.strftime("%Y-%m-%d"))
        data["datasets"][0]["data"].append(total_seconds)
    return data


###############
# SteamGridDB
###############


@app.get("/api/sgdb/search", tags=["SteamGridDB"])
def search_sgdb(query: str):
    cache_key = f"sgdb_search_{query}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        return cached
    return cacheSetReturn(cache_key, steamgriddb.search(query))


@app.get("/api/sgdb/grids/{game_id}", tags=["SteamGridDB"])
def grid_sgdb(game_id: int):
    cache_key = f"sgdb_grids_{game_id}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        return cached
    return cacheSetReturn(cache_key, steamgriddb.get_grids(game_id))


@app.get("/api/sgdb/grids/{game_id}/best", tags=["SteamGridDB"])
def best_grid_sgdb(game_id: int):
    cache_key = f"sgdb_best_grid_{game_id}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        if isinstance(cached, HTTPException):
            logger.warning("Returning a cached exception! 🤔 %s", cache_key)
            raise cached
        return cached

    best = steamgriddb.get_best_grid(game_id)
    if not best:
        # caching an exception seems cursed...
        logger.warning("CACHING AN EXCEPTION! 🤔 %s", cache_key)
        raise cacheSetReturn(
            cache_key, HTTPException(status_code=404, detail="Not found")
        )

    return cacheSetReturn(cache_key, best)


###############
# Discord
###############


@app.get("/api/discord/{discord_user_id}/avatar", tags=["Discord"])
def get_discord_avatar(discord_user_id: int):
    cache_key = f"discord_avatar_{discord_user_id}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        return cached

    logger.debug("Fetching avatar for user %s from Discord", discord_user_id)
    url = bot.avatar_from_discord_user_id(discord_user_id)
    res = {"url": url}
    return cacheSetReturn(cache_key, res)
