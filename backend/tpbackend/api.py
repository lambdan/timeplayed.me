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
from tpbackend.utils import (
    clamp,
    max_int as max,
    roundToSecond,
    validateTS,
    tsFromActivity,
)
from tpbackend import bot
from tpbackend import steamgriddb
from tpbackend.storage.storage_v2 import User, Game, Platform, Activity
from tpbackend.cache import cache_set, cache_get
import logging

logger = logging.getLogger("api")

app = FastAPI()


def not_found(msg: str):
    raise HTTPException(status_code=404, detail=msg)


# def fixDatetime(data):
#    """
#    Recursively converts datetime objects in a dictionary to milliseconds since epoch
#    """
#    if isinstance(data, datetime.datetime):
#        if data.tzinfo is None:
#            data = data.replace(tzinfo=datetime.timezone.utc)
#        return int(data.timestamp() * 1000)
#
#    if not isinstance(data, (dict, list)):
#        return data
#
#    if isinstance(data, dict):
#        return {k: fixDatetime(v) for k, v in data.items()}
#
#    if isinstance(data, list):
#        return [fixDatetime(item) for item in data]


def get_public_user_by_id(userId: int) -> PublicUserModel | None:
    user = User.get_or_none(User.id == userId)
    if not user:
        return None
    return get_public_user(user)


def get_public_user(user: User) -> PublicUserModel:
    key = f"get_public_user:{user.id}"
    cached = cache_get(key)
    if cached:
        decoded = cached.decode("utf-8")  # type: ignore
        return PublicUserModel.model_validate_json(decoded)

    avatar_url = None
    if user.discord_id:
        avatar_url = get_discord_avatar_url(str(user.discord_id))
    r = PublicUserModel(
        id=int(user.id),  # type: ignore
        discord_id=str(user.discord_id),
        name=str(user.name),
        avatar_url=avatar_url,
        default_platform=PublicPlatformModel(
            id=user.default_platform.id,
            abbreviation=user.default_platform.abbreviation,
            name=user.default_platform.name,
            color_primary=user.default_platform.color_primary,
            color_secondary=user.default_platform.color_secondary,
            icon=user.default_platform.icon,
        ),
    )
    cache_set(key, r.model_dump_json())
    return r


def get_public_activity_by_id(activityId: int) -> PublicActivityModel | None:
    activity = Activity.get_or_none(Activity.id == activityId)  # type: ignore
    if not activity:
        return None
    return get_public_activity(activity)


def get_public_activity(activity: Activity) -> PublicActivityModel:
    key = f"get_public_activity:{activity.id}"
    cached = cache_get(key)
    if cached:
        decoded = cached.decode("utf-8")  # type: ignore
        return PublicActivityModel.model_validate_json(decoded)

    user = get_public_user(activity.user)  # type: ignore
    r = PublicActivityModel(
        id=activity.id,  # type: ignore
        timestamp=tsFromActivity(activity),
        user=user,
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
            color_primary=activity.platform.color_primary,
            color_secondary=activity.platform.color_secondary,
            icon=activity.platform.icon,
        ),
        seconds=activity.seconds,  # type: ignore
        emulated=activity.emulated,  # type: ignore
    )
    cache_set(key, r.model_dump_json(), ex=5)
    return r


####################
# Users
####################


def user_has_activities(userId: int) -> bool:
    """
    Returns True if user has any activities
    """
    any_activity = Activity.select().where(Activity.user == userId).first()
    return any_activity is not None


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
    return PaginatedUserWithStats(
        data=data,
        total=total,
        offset=offset,
        limit=limit,
    )


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
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> PaginatedActivities:

    limit = clamp(limit, 1, 500)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)
    if before:
        before = roundToSecond(before)
    if after:
        after = roundToSecond(after)
    key = f"get_activities:{offset}:{limit}:{order}:{user}:{game}:{platform}:{before}:{after}"
    cached = cache_get(key)
    if cached:
        return PaginatedActivities.model_validate_json(cached.decode("utf-8"))  # type: ignore

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

    data = []
    for a in query:
        data.append(get_public_activity(a))

    r = PaginatedActivities(
        data=data,
        total=total_count,
        offset=offset,
        limit=limit,
        order=order,
    )

    cache_set(key, r.model_dump_json(), ex=15)
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
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    platformId: int | None = None,
) -> GameWithStats:
    game = Game.get_or_none(Game.id == gameId)  # type: ignore
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    def redisGet(key: str) -> GameWithStats | None:
        raw = cache_get(key)
        if raw:
            try:
                decoded = raw.decode("utf-8")  # type: ignore
                parsed = GameWithStats.model_validate_json(decoded)
                # logger.info("✅ Hit cache %s", key)
                return parsed
            except Exception as _:
                logger.warning("Exception when parsing redis cache on key %s", key)
        return None

    cache_key = f"game_with_stats:{gameId}:{userId}:{before}:{after}:{platformId}"
    cached = redisGet(cache_key)
    if cached:
        return cached

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

    cache_set(cache_key, r.model_dump_json())
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
    userId: int | None = None,
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
        color_primary=pf.color_primary,
        color_secondary=pf.color_secondary,
        icon=pf.icon,
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
    userId: int | None = None,
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
    userId: str | None = None, gameId: int | None = None, platformId: int | None = None
):
    query = Activity.select(Activity.timestamp, Activity.seconds)
    conditions = []
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        conditions.append(Activity.game == gameId)
    if platformId:
        conditions.append(Activity.platform == platformId)
    if conditions:
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


###############
# Discord
###############


def get_discord_avatar_url(discord_user_id: str | int) -> str:
    discord_user_id = int(discord_user_id)
    cache_key = f"2_discord_avatar_{discord_user_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached.decode("utf-8")  # type: ignore
    url = bot.avatar_from_discord_user_id(discord_user_id)
    cache_set(cache_key, url, ex=3600)
    return url
