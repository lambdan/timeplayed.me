import datetime
import os
from typing import Literal
from fastapi import FastAPI, HTTPException
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
from tpbackend.utils import clamp, max_int as max, today, thisHour, validateTS
from tpbackend import bot
from tpbackend import steamgriddb
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


def get_public_user(userId: str) -> PublicUserModel | None:
    user = User.get_or_none(User.id == userId)
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


def user_has_activities(userId: str) -> bool:
    """
    Returns True if user has any activities
    """
    any_activity = Activity.select().where(Activity.user == userId).first()
    return any_activity != None


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

    total = get_user_count(
        before=before, after=after, gameId=gameId, platformId=platformId
    )

    filters = []
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

    query = Activity.select()
    if len(filters) > 0:
        query = query.where(*filters)
    query = query.order_by(Activity.user.asc()).distinct(Activity.user)
    activities = query[offset : offset + limit]  # type: ignore

    data = []
    for a in activities:
        userId = str(a.user.id)
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
    return PaginatedUserWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )


@app.get("/api/user/{userId}", tags=["users"], response_model=UserWithStats)
def get_user(
    userId: str,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
) -> UserWithStats:
    user = get_public_user(userId)
    if not user or not user_has_activities(userId):
        raise HTTPException(status_code=404, detail="User not found")

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
    user: str | None = None,
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


def get_oldest_or_newest_activity(
    oldest: bool,
    userid: str | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PublicActivityModel | None:
    order = "asc" if oldest else "desc"
    activities = get_activities(
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


def get_newest_activity(
    userid: str | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PublicActivityModel | None:
    return get_oldest_or_newest_activity(
        oldest=False, userid=userid, gameid=gameid, platformid=platformid
    )


def get_oldest_activity(
    userid: str | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PublicActivityModel | None:
    return get_oldest_or_newest_activity(
        oldest=True, userid=userid, gameid=gameid, platformid=platformid
    )


@app.get(
    "/api/activities/{activity_id}",
    tags=["activities"],
    response_model=PublicActivityModel,
)
def get_activity(activity_id: int) -> PublicActivityModel:
    activity = Activity.get_or_none(Activity.id == activity_id)  # type: ignore
    if activity == None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return get_public_activity(activity)


##############
# Games
#############


@app.get("/api/games", tags=["games"], response_model=PaginatedGameWithStats)
def get_games(
    offset=0,
    limit=25,
    userId: str | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedGameWithStats:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    filters = []
    if userId:
        filters.append(Activity.user == userId)
    if platformId:
        filters.append(Activity.platform == platformId)
    if before:
        before_dt = datetime.datetime.fromtimestamp(before / 1000)
        filters.append(Activity.timestamp <= before_dt)  # type: ignore
    if after:
        after_dt = datetime.datetime.fromtimestamp(after / 1000)
        filters.append(Activity.timestamp >= after_dt)  # type: ignore

    query = Activity.select()
    if len(filters) > 0:
        query = query.where(*filters)
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
    return PaginatedGameWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )


@app.get("/api/game/{gameId}", tags=["games"], response_model=GameWithStats)
def get_game(
    gameId: int,
    userId: str | None = None,
    before: int | None = None,
    after: int | None = None,
    platformId: int | None = None,
) -> GameWithStats:
    game = Game.get_or_none(Game.id == gameId)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    gameModel = PublicGameModel(
        id=game.id,
        name=game.name,
        steam_id=game.steam_id,
        sgdb_id=game.sgdb_id,
        image_url=game.image_url,
        aliases=game.aliases,
        release_year=game.release_year,
    )

    totals = get_totals(
        userId=userId, gameId=game.id, before=before, after=after, platformId=platformId
    )

    total_playtime_all_games = get_total_playtime(
        userId=userId, before=before, after=after, platformId=platformId
    )
    total_playtime_this_game = get_total_playtime(
        userId=userId, gameId=game.id, before=before, after=after, platformId=platformId
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
            gameid=game.id,
            before=before,
            after=after,
            platformid=platformId,
        ),
        newest_activity=get_newest_activity(
            userid=userId,
            gameid=game.id,
            before=before,
            after=after,
            platformid=platformId,
        ),
    )

    return r


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


##############
# Platforms
##############


@app.get("/api/platforms", tags=["games"], response_model=PaginatedPlatformsWithStats)
def get_platforms(
    offset=0,
    limit=25,
    userId: str | None = None,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedPlatformsWithStats:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    filters = []
    if userId:
        filters.append(Activity.user == userId)
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
    return PaginatedPlatformsWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )


@app.get(
    "/api/platform/{platformId}", tags=["platforms"], response_model=PlatformWithStats
)
def get_platform(
    platformId: int,
    userId: str | None = None,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
) -> PlatformWithStats:
    pf = Platform.get_or_none(Platform.id == platformId)  # type: ignore
    if not pf:
        raise HTTPException(status_code=404, detail="Platform not found")

    platformModel = PublicPlatformModel(
        id=pf.id,
        abbreviation=pf.abbreviation,
        name=pf.name,
    )

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
    userId: str | None = None,
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


def get_total_playtime(
    userId: str | None = None,
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


def get_activity_count(
    userId: str | None = None,
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


def get_user_count(
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
) -> int:
    # total = 0
    # for user in User.select():
    #     if get_activity_count(userId=user.id, before=before, after=after, gameId=gameId, platformId=platformId) > 0:
    #         total += 1
    # return total
    conditions = []
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
        return Activity.select(Activity.user).where(*conditions).distinct().count()
    return Activity.select(Activity.user).distinct().count()


def get_game_count(
    userId: str | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> int:
    # iterating over Activity to only get games with activity
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)

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
        return Activity.select(Activity.game).where(*conditions).distinct().count()
    return Activity.select(Activity.game).distinct().count()


def get_platform_count(
    userId: str | None = None,
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
    userId: str | None = None, gameId: int | None = None, platformId: int | None = None
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


@app.get(
    "/api/sgdb/search",
    tags=["SteamGridDB"],
    response_model=list[steamgriddb.SGDB_Game_SearchResult],
)
def search_sgdb(query: str) -> list[steamgriddb.SGDB_Game_SearchResult]:
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
