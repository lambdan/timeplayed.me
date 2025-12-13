import datetime
import os
from fastapi import FastAPI, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn
from tpbackend.utils import clamp, max_int as max, today, thisHour, validateTS
from tpbackend import bot
from tpbackend import steamgriddb
from tpbackend.models import (
    GameWithStats,
    PaginatedResponse,
    PlatformWithStats,
    UserWithStats,
)
from tpbackend.storage.storage_v2 import LiveActivity, User, Game, Platform, Activity
import logging

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


def get_public_user(userId: int) -> User | None:
    user = User.get_or_none(User.id == userId)
    if not user:
        return None
    return model_to_dict(user, exclude=[User.bot_commands_blocked, User.default_platform])  # type: ignore


def clean_activity(activity: Activity | dict) -> dict:
    if not isinstance(activity, dict):
        activity = model_to_dict(activity)
    if "user" in activity and isinstance(activity["user"], dict):
        activity["user"].pop("bot_commands_blocked", None)
        activity["user"].pop("default_platform", None)
    return activity


####################
# Users
####################


@app.get("/api/users/{userId}")
def get_user(userId: int):
    user = get_public_user(userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_activities = get_activity_count(userId=userId)
    if total_activities == 0:
        logger.warning("User %s has no activities, returning 404", user.id)
        raise HTTPException(status_code=404, detail="User not found")

    data: UserWithStats = {
        "user": user,
        "last_played": get_last_activity(userid=userId)["timestamp"],  # type: ignore
        "total_activities": total_activities,
        "total_playtime": get_total_playtime(userId=userId),
    }
    return fixDatetime(data)


@app.get("/api/users")
def get_users(offset=0, limit=25):
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    response: PaginatedResponse = {
        "data": [],
        "_total": get_user_count(),
        "_offset": offset,
        "_limit": limit,
    }
    for user in User.select().limit(limit).offset(offset):
        try:
            response["data"].append(get_user(user.id))
        except:
            logger.warning("Skipping user %s in get_users", user.id)
            continue
    return fixDatetime(response)


@app.get("/api/users/{userId}/games")
def get_user_games(userId: int, offset=0, limit=25):
    offset = max(0, offset)
    limit = clamp(limit, 1, 100)
    user = get_public_user(userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = Activity.select(Activity.game).where(Activity.user == userId).distinct()
    games = games[offset : offset + limit]  # type: ignore
    response = []
    for game in games:
        game_data = get_game(gameId=game.game.id, userId=userId)
        response.append(game_data)

    paginatedResponse: PaginatedResponse = {
        "data": response,
        "_total": get_game_count(userId=userId),
        "_offset": offset,
        "_limit": limit,
    }

    return fixDatetime(paginatedResponse)


@app.get("/api/users/{userId}/platforms")
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
                    "last_played": get_last_activity(userid=userId, platformid=platform.id)["timestamp"],  # type: ignore
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


@app.get("/api/users/{user_id}/stats")
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

    oldest_activity = clean_activity(oldest_activity) if oldest_activity else None
    newest_activity = clean_activity(newest_activity) if newest_activity else None

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


@app.get("/api/activities")
def list_activities(
    offset=0,
    limit=25,
    order="desc",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before=None,
    after=None,
):
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

    total_count = (
        Activity.select().where(*filters).count()
        if filters
        else Activity.select().count()
    )

    response = {
        "data": [clean_activity(activity) for activity in query],
        "_total": total_count,
        "_offset": offset,
        "_limit": limit,
        "_order": order,
        "_before": before_dt.isoformat() if before_dt else None,
        "_after": after_dt.isoformat() if after_dt else None,
    }
    response = fixDatetime(response)
    return cacheSetReturn(cache_key, response)


@app.get("/api/activities/last")
def get_last_activity(
    userid: int | None = None, gameid: int | None = None, platformid: int | None = None
):
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

    return fixDatetime(model_to_dict(last_activity))


@app.get("/api/activities/live")
def get_live_activities():
    live_activities = LiveActivity.select()
    return fixDatetime([clean_activity(activity) for activity in live_activities])


@app.get("/api/activities/{activity_id}")
def get_activity(activity_id: int):
    activity = Activity.get_or_none(Activity.id == activity_id)  # type: ignore
    return fixDatetime(model_to_dict(activity)) if activity else {"error": "Not found"}


##############
# Games
#############


@app.get("/api/games")
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

    paginatedResponse: PaginatedResponse = {
        "data": response,
        "_total": get_game_count(),
        "_offset": offset,
        "_limit": limit,
    }

    return fixDatetime(paginatedResponse)


@app.get("/api/games/{gameId}")
def get_game(gameId: int, userId: int | None = None):
    game = Game.get_or_none(Game.id == gameId)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    entry: GameWithStats = {
        "game": model_to_dict(game),  # type: ignore
        "total_playtime": get_total_playtime(userId=userId, gameId=game.id),
        "last_played": get_last_activity(userid=userId, gameid=game.id)["timestamp"],  # type: ignore
        "total_sessions": get_activity_count(userId=userId, gameId=game.id),
    }

    return fixDatetime(entry)


@app.get("/api/games/{game_id}/stats")
def get_game_stats(game_id: int):
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
    player_count = (
        Activity.select(Activity.user).where(Activity.game == game).distinct().count()
    )

    return fixDatetime(
        {
            "total_playtime": total_playtime,
            "activity_count": activity_count,
            "platform_count": platform_count,
            "player_count": player_count,
            "oldest_activity": (
                clean_activity(model_to_dict(oldest_activity))
                if oldest_activity
                else None
            ),
            "newest_activity": (
                clean_activity(model_to_dict(newest_activity))
                if newest_activity
                else None
            ),
        }
    )


@app.get("/api/games/{gameId}/players")
def get_game_players(gameId: int):
    game = Game.get_or_none(Game.id == gameId)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players = []
    for user in User.select():
        total_playtime = get_total_playtime(userId=user.id, gameId=game.id)
        if total_playtime > 0:
            players.append(
                {
                    "user": get_public_user(user.id),
                    "total_playtime": total_playtime,
                    "last_played": get_last_activity(userid=user.id, gameid=game.id)["timestamp"],  # type: ignore
                    "total_sessions": get_activity_count(
                        userId=user.id, gameId=game.id
                    ),
                }
            )
    return fixDatetime(players)


@app.get("/api/games/{gameId}/platforms")
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
@app.get("/api/platforms/{platform_id}")
def get_platform(platform_id: int):
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

    data: PlatformWithStats = {
        "platform": model_to_dict(platform),  # type: ignore
        "last_played": Activity.select(fn.MAX(Activity.timestamp))
        .where(Activity.platform == platform)
        .scalar()
        or None,
        "total_sessions": Activity.select()
        .where(Activity.platform == platform)
        .count(),
        "total_playtime": playtime_this_platform,
        "percent": playtime_this_platform / total_playtime_all_platforms,
    }
    return fixDatetime(data)


@app.get("/api/platforms")
def list_platforms(offset=0, limit=25):
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    platforms = Platform.select().limit(limit).offset(offset)

    response: PaginatedResponse = {
        "data": [],  # type: ignore
        "_total": Platform.select().count(),
        "_offset": offset,
        "_limit": limit,
    }

    for platform in platforms:
        response["data"].append(get_platform(platform.id))
    return fixDatetime(response)


#################
# Totals
#################


@app.get("/api/stats")
def get_stats():
    return {
        "total_playtime": get_total_playtime(),
        "activities": get_activity_count(),
        "users": get_user_count(),
        "games": get_game_count(),
        "platforms": get_platform_count(),
    }


@app.get("/api/stats/total_playtime")
def get_total_playtime(
    userId: int | None = None, gameId: int | None = None, platformId: int | None = None
) -> int:
    query = Activity.select(fn.SUM(Activity.seconds))
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)
    if conditions:
        query = query.where(*conditions)
    return query.scalar() or 0


@app.get("/api/stats/total_activities")
def get_activity_count(
    userId: int | None = None, gameId: int | None = None, platformId: int | None = None
) -> int:
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)
    if len(conditions) > 0:
        return Activity.select().where(*conditions).count()
    return Activity.select().count()


@app.get("/api/stats/total_users")
def get_user_count() -> int:
    total = 0
    for user in User.select():
        if get_activity_count(userId=user.id) > 0:
            total += 1
    return total


@app.get("/api/stats/total_games")
def get_game_count(userId: int | None = None) -> int:
    # iterating over Activity to only get games with activity
    if userId:
        return (
            Activity.select(Activity.game)
            .where(Activity.user == userId)
            .distinct()
            .count()
        )
    return Activity.select(Activity.game).distinct().count()


@app.get("/api/stats/total_platforms")
def get_platform_count(userId: int | None = None, gameId: int | None = None) -> int:
    if userId and gameId:
        return (
            Activity.select(Activity.platform)
            .where((Activity.user == userId) & (Activity.game == gameId))
            .distinct()
            .count()
        )
    if userId:
        return (
            Activity.select(Activity.platform)
            .where(Activity.user == userId)
            .distinct()
            .count()
        )
    if gameId:
        return (
            Activity.select(Activity.platform)
            .where(Activity.game == gameId)
            .distinct()
            .count()
        )
    return Activity.select(Activity.platform).distinct().count()


##############
# For chart.js
##############


@app.get("/api/stats/chart/playtime_by_day")
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


@app.get("/api/sgdb/search")
def search_sgdb(query: str):
    cache_key = f"sgdb_search_{query}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        return cached
    return cacheSetReturn(cache_key, steamgriddb.search(query))


@app.get("/api/sgdb/grids/{game_id}")
def grid_sgdb(game_id: int):
    cache_key = f"sgdb_grids_{game_id}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        return cached
    return cacheSetReturn(cache_key, steamgriddb.get_grids(game_id))


@app.get("/api/sgdb/grids/{game_id}/best")
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


@app.get("/api/discord/{discord_user_id}/avatar")
def get_discord_avatar(discord_user_id: int):
    cache_key = f"discord_avatar_{discord_user_id}_{today()}"
    cached = cacheGet(cache_key)
    if cached:
        return cached

    logger.debug("Fetching avatar for user %s from Discord", discord_user_id)
    url = bot.avatar_from_discord_user_id(discord_user_id)
    res = {"url": url}
    return cacheSetReturn(cache_key, res)
