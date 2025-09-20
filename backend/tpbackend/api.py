import datetime
from fastapi import FastAPI, HTTPException
from playhouse.shortcuts import model_to_dict
from peewee import fn

from tpbackend import bot
from tpbackend import steamgriddb
from tpbackend.models import GameWithStats, PaginatedResponse, PlatformWithStats, UserWithStats
from tpbackend.storage.storage_v2 import LiveActivity, User, Game, Platform, Activity
import time
import logging

logger = logging.getLogger("api")

app = FastAPI()

def validateLimitOffset(limit: int|str, offset: int|str, maxLimit=50) -> tuple[int, int]:
    """
    Returns `[ limit , offset ]`
    """
    try:
        offset = max(0, int(offset))
    except:
        offset = 0

    try:
        limit = max(1, min(maxLimit, int(limit)))
    except:
        limit = maxLimit
    
    return limit, offset

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


@app.get("/api/users/{userId}")
def get_user(userId: int):
    user = User.get_or_none(User.id == userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_activities = get_activity_count(userId=user.id)
    if total_activities == 0:
        logger.warning("User %s has no activities, returning 404", user.id)
        raise HTTPException(status_code=404, detail="User not found")

    data: UserWithStats = {
        "user": model_to_dict(user, exclude=[User.bot_commands_blocked, User.default_platform]),  # type: ignore
        "last_played": get_last_activity(userid=user.id)["timestamp"], # type: ignore
        "total_activities":  total_activities,
        "total_playtime":  get_total_playtime(userId=user.id),
    }
    return fixDatetime(data)

@app.get("/api/users")
def get_users(offset=0, limit=25):
    limit, offset = validateLimitOffset(limit, offset)
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
def get_user_games(userId: int, offset = 0, limit = 25):
    limit, offset = validateLimitOffset(limit, offset)
    user = User.get_or_none(User.id == userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = Activity.select(Activity.game).where(Activity.user == userId).distinct()
    games = games[int(offset):int(offset) + int(limit)]  # type: ignore
    response = []
    for game in games:
        game_data = get_game(gameId=game.game.id, userId=user.id)
        response.append(game_data)

    paginatedResponse: PaginatedResponse = {
        "data": response,
        "_total": get_game_count(userId=user.id),
        "_offset": offset,
        "_limit": limit,
    }

    return fixDatetime(paginatedResponse)

@app.get("/api/users/{userId}/platforms")
def get_user_platforms(userId: int):
    user = User.get_or_none(User.id == userId) # type: ignore
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    platforms = []
    for platform in Platform.select():
        total_playtime = get_total_playtime(userId=user.id, platformId=platform.id)
        if total_playtime > 0:
            platforms.append({
                "platform": model_to_dict(platform),  # type: ignore
                "total_playtime": total_playtime,
                "last_played": get_last_activity(userid=user.id, platformid=platform.id)["timestamp"], # type: ignore
                "total_sessions": get_activity_count(userId=user.id, platformId=platform.id),
                "percent": total_playtime / get_total_playtime(userId=user.id) if get_total_playtime(userId=user.id) > 0 else 0
            })
    return fixDatetime(platforms)


@app.get("/api/users/{user_id}/stats")
def get_user_stats(user_id: int):
    user = User.get_or_none(User.id == user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    oldest_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.asc()).first()
    newest_activity = Activity.select().where(Activity.user == user).order_by(Activity.timestamp.desc()).first()
    total_playtime = get_total_playtime(userId=user.id)
    total_activities = get_activity_count(userId=user.id)
    total_games = get_game_count(userId=user.id)
    total_platforms = get_platform_count(userId=user.id)

    return fixDatetime({
        "total": {
            "seconds": total_playtime,
            "activities": total_activities,
            "games": total_games,
            "platforms": total_platforms
        },
        "oldest_activity": model_to_dict(oldest_activity) if oldest_activity else None,
        "newest_activity": model_to_dict(newest_activity) if newest_activity else None,
        "active_days": Activity.select(fn.COUNT(fn.DISTINCT(fn.DATE(Activity.timestamp)))).where(Activity.user == user).scalar(),
        "average": {
            "seconds_per_game": total_playtime / total_games if total_games > 0 else 0,
            "sessions_per_game": total_activities / total_games if (total_activities > 0 and total_games > 0) else 0,
            "session_length": total_playtime / total_activities if (total_activities > 0 and total_playtime > 0) else 0,
        }
    })

#################
# Activities
#################

@app.get("/api/activities")
def list_activities(offset = 0, limit = 25, order = "desc", user: int | None = None, game: int | None = None, platform: int | None = None):
    limit, offset = validateLimitOffset(limit, offset, maxLimit=500)
    activities = [model_to_dict(activity) for activity in 
        Activity.select().offset(offset).limit(limit).order_by(Activity.timestamp.desc() if order == "desc" else Activity.timestamp.asc())
        .where(
            (Activity.user == user) if user is not None else True,
            (Activity.game == game) if game is not None else True,
            (Activity.platform == platform) if platform is not None else True
        )]
    response = {
        "data": activities,
        "_total": Activity.select().where(
            (Activity.user == user) if user is not None else True,
            (Activity.game == game) if game is not None else True,
            (Activity.platform == platform) if platform is not None else True
        ).count(),
        "_offset": offset,
        "_limit": limit,
        "_order": order
    }
    return fixDatetime(response)


@app.get("/api/activities/{activity_id}")
def get_activity(activity_id: int):
    activity = Activity.get_or_none(Activity.id == activity_id) # type: ignore
    return fixDatetime(model_to_dict(activity)) if activity else {"error": "Not found"}

@app.get("/api/activities/last")
def get_last_activity(userid: int | None = None, gameid: int | None = None, platformid: int | None = None):
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
    return fixDatetime([model_to_dict(activity) for activity in live_activities])

##############
# Games
#############

@app.get("/api/games")
def get_games(limit = 25, offset = 0):
    limit, offset = validateLimitOffset(limit, offset)

    # Could not get .offset and .limit to work with distinct so have to do a extra step
    games = Activity.select(Activity.game).distinct()
    games = games[int(offset):int(offset) + int(limit)]  # type: ignore
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
    game = Game.get_or_none(Game.id == gameId) # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    entry: GameWithStats ={
        "game": model_to_dict(game),  # type: ignore
        "total_playtime": get_total_playtime(userId=userId, gameId=game.id),
        "last_played": get_last_activity(userid=userId, gameid=game.id)["timestamp"], # type: ignore
        "total_sessions": get_activity_count(userId=userId, gameId=game.id),
    }

    return fixDatetime(entry)

@app.get("/api/games/{game_id}/stats")
def get_game_stats(game_id: int):
    game = Game.get_or_none(Game.id == game_id) # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    oldest_activity = Activity.select().where(Activity.game == game).order_by(Activity.timestamp.asc()).first()
    newest_activity = Activity.select().where(Activity.game == game).order_by(Activity.timestamp.desc()).first()
    total_playtime = get_total_playtime(gameId=game.id)
    activity_count = get_activity_count(gameId=game.id)
    platform_count = get_platform_count(gameId=game.id)
    player_count = Activity.select(Activity.user).where(Activity.game == game).distinct().count()

    return fixDatetime({
        "total_playtime": total_playtime,
        "activity_count": activity_count,
        "platform_count": platform_count,
        "player_count": player_count,
        "oldest_activity": model_to_dict(oldest_activity) if oldest_activity else None,
        "newest_activity": model_to_dict(newest_activity) if newest_activity else None,
    })

@app.get("/api/games/{gameId}/players")
def get_game_players(gameId: int):
    game = Game.get_or_none(Game.id == gameId) # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    players = []
    for user in User.select():
        total_playtime = get_total_playtime(userId=user.id, gameId=game.id)
        if total_playtime > 0:
            players.append({
                "user": model_to_dict(user),  # type: ignore
                "total_playtime": total_playtime,
                "last_played": get_last_activity(userid=user.id, gameid=game.id)["timestamp"], # type: ignore
                "total_sessions": get_activity_count(userId=user.id, gameId=game.id),
            })
    return fixDatetime(players)

@app.get("/api/games/{gameId}/platforms")
def get_game_platforms(gameId: int):
    game = Game.get_or_none(Game.id == gameId) # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    platforms = []
    for platform in Platform.select():
        total_playtime = get_total_playtime(gameId=game.id, platformId=platform.id)
        if total_playtime > 0:
            platforms.append({
                "platform": model_to_dict(platform),  # type: ignore
                "total_playtime": total_playtime,
                "last_played": get_last_activity(gameid=game.id, platformid=platform.id)["timestamp"], # type: ignore
                "total_sessions": get_activity_count(gameId=game.id, platformId=platform.id),
                "percent": total_playtime / get_total_playtime(gameId=game.id) if get_total_playtime(gameId=game.id) > 0 else 0
            })
    return fixDatetime(platforms)


##############
# Platforms
##############
@app.get("/api/platforms/{platform_id}")
def get_platform(platform_id: int):
    platform = Platform.get_or_none(Platform.id == platform_id) # type: ignore
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    total_playtime_all_platforms = get_total_playtime()
    playtime_this_platform = Activity.select(fn.SUM(Activity.seconds)).where(Activity.platform == platform).scalar() or 0

    data: PlatformWithStats = {
        "platform": model_to_dict(platform), # type: ignore
        "last_played": Activity.select(fn.MAX(Activity.timestamp)).where(Activity.platform == platform).scalar() or None,
        "total_sessions": Activity.select().where(Activity.platform == platform).count(),
        "total_playtime": playtime_this_platform,
        "percent": playtime_this_platform / total_playtime_all_platforms 
    } 
    return fixDatetime(data)

@app.get("/api/platforms")
def list_platforms(offset=0, limit=25):
    limit, offset = validateLimitOffset(limit, offset)
    platforms = Platform.select().limit(limit).offset(offset)

    response: PaginatedResponse = {
        "data": [], # type: ignore
        "_total": Platform.select().count() ,
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
def get_total_playtime(userId: int | None = None, gameId: int | None = None, platformId: int | None = None) -> int:
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
def get_activity_count(userId: int | None = None, gameId: int | None = None, platformId: int | None = None) -> int:
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
        return Activity.select(Activity.game).where(Activity.user == userId).distinct().count()
    return Activity.select(Activity.game).distinct().count()

@app.get("/api/stats/total_platforms")
def get_platform_count(userId: int | None = None, gameId: int | None = None) -> int:
    if userId and gameId:
        return Activity.select(Activity.platform).where(
            (Activity.user == userId) & (Activity.game == gameId)
        ).distinct().count()
    if userId:
        return Activity.select(Activity.platform).where(
            Activity.user == userId
        ).distinct().count()
    if gameId:
        return Activity.select(Activity.platform).where(
            Activity.game == gameId
        ).distinct().count()
    return Activity.select(Activity.platform).distinct().count()

##############
# For chart.js
##############

@app.get("/api/stats/chart/playtime_by_day")
def get_playtime_by_day(userId: int | None = None, gameId: int | None = None, platformId: int | None = None):
    query = Activity.select(
        fn.DATE(Activity.timestamp).alias('date'),
        fn.SUM(Activity.seconds).alias('total_seconds')
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
    data = {
        "labels": [],
        "datasets": [{
            "label": "Playtime (seconds)",
            "data": []
        }]
    }
    for date, total_seconds in results:
        data["labels"].append(date.strftime("%Y-%m-%d"))
        data["datasets"][0]["data"].append(total_seconds)
    return data
    


###############
# SteamGridDB
###############

@app.get("/api/sgdb/search")
def search_sgdb(query: str):
    return steamgriddb.search(query)

@app.get("/api/sgdb/grids/{game_id}")
def grid_sgdb(game_id: int):
    grids = steamgriddb.get_grids(game_id)
    return grids 

@app.get("/api/sgdb/grids/{game_id}/best")
def best_grid_sgdb(game_id: int):
    best = steamgriddb.get_best_grid(game_id)
    if not best:
        raise HTTPException(status_code=404, detail="Not found")
    return best

###############
# Discord
###############

discord_avatar_cache = {}
@app.get("/api/discord/{discord_user_id}/avatar")
def get_discord_avatar(discord_user_id: int):
    now = time.time()
    cache_entry = discord_avatar_cache.get(discord_user_id)
    if cache_entry:
        url, timestamp = cache_entry
        if now - timestamp < 3600:  # 1 hour cache
            logger.debug("Returning cached avatar for user %s", discord_user_id)
            return {"url": url}
    logger.debug("Fetching avatar for user %s from Discord", discord_user_id)
    url = bot.avatar_from_discord_user_id(discord_user_id)
    discord_avatar_cache[discord_user_id] = (url, now)
    return {"url": url}