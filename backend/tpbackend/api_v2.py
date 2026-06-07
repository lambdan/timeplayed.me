import datetime
from typing import Literal, cast
from peewee import fn
from tpbackend.api_v2_models import (
    GameStatsV2,
    PlatformStatsV2,
    PublicActivityModelV2,
    PublicGameModelV2,
    PublicPlatformModelV2,
    PublicUserModelV2,
    UserStatsV2,
)
from tpbackend.utils import (
    search_games_for_api,
)
from tpbackend.utils2 import (
    clamp,
    max_int as max,
    validateTS,
)
from tpbackend.storage.storage_v2 import (
    Activity_or_none,
    Game_or_none,
    Platform_or_none,
    Activity,
    User_or_none,
)
from tpbackend.api_responses import bad_request, not_found
from tpbackend.api import get_totals  # grab FastAPI from API v1
import logging

from fastapi import APIRouter

logger = logging.getLogger("api_v2")
router = APIRouter()


ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712


################ HELPERS ##################


def get_total_playtime(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> int:
    query = Activity.select(Activity.seconds)
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        game = Game_or_none(gameId)
        if game:
            game_ids = [gameId]
            if include_game_children:
                for child in game.get_children():
                    game_ids.append(child.get_id())
            conditions.append(Activity.game.in_(game_ids))  # type: ignore
        else:
            return 0
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    query = query.where(*conditions)
    total = query.select(fn.SUM(Activity.seconds)).scalar() or 0
    return total


def get_activity_count(
    userId: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        game = Game_or_none(gameId)
        if game:
            game_ids = [gameId]
            if include_game_children:
                for child in game.get_children():
                    game_ids.append(child.get_id())
            conditions.append(Activity.game.in_(game_ids))  # type: ignore
        else:
            return 0
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    r = Activity.select().where(*conditions).count()
    return r


def get_user_count(
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
    include_game_children: bool = False,
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if gameId:
        game = Game_or_none(gameId)
        if game:
            game_ids = [gameId]
            if include_game_children:
                for child in game.get_children():
                    game_ids.append(child.get_id())
            conditions.append(Activity.game.in_(game_ids))  # type: ignore
        else:
            return 0
    if platformId:
        conditions.append(Activity.platform == platformId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    r = Activity.select(Activity.user).where(*conditions).distinct().count()
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
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    r = Activity.select(Activity.game).where(*conditions).distinct().count()
    return r


def get_platform_count(
    userId: int | None = None,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    if userId:
        conditions.append(Activity.user == userId)
    if gameId:
        game = Game_or_none(gameId)
        if game:
            game_ids = [gameId]
            if include_game_children:
                for child in game.get_children():
                    game_ids.append(child.get_id())
            conditions.append(Activity.game.in_(game_ids))  # type: ignore
        else:
            return 0

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    r = Activity.select(Activity.platform).where(*conditions).distinct().count()
    return r


def get_player_count(
    gameId: int, before: int | None = None, after: int | None = None
) -> int:
    conditions = ACTIVITY_BASE_FILTERS.copy()
    conditions.append(Activity.game == gameId)

    before_valid, after_valid = validateTS(before), validateTS(after)
    before_dt, after_dt = None, None
    if before_valid:
        before_dt = datetime.datetime.fromtimestamp(before_valid / 1000)
        conditions.append(Activity.timestamp <= before_dt)  # type: ignore
    if after_valid:
        after_dt = datetime.datetime.fromtimestamp(after_valid / 1000)
        conditions.append(Activity.timestamp >= after_dt)  # type: ignore

    r = Activity.select(Activity.user).where(*conditions).distinct().count()
    return r


def get_oldest_or_newest_activity_id(
    oldest: bool,
    userid: int | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> int | None:
    order = "asc" if oldest else "desc"
    activities = get_activities_ids_impl(
        offset=0,
        limit=1,
        order=order,
        user=userid,
        game=gameid,
        platform=platformid,
        before=before,
        after=after,
        include_game_children=include_game_children,
    )
    if len(activities) == 0:
        return None
    return activities[0]


def user_has_activities(userId: int) -> bool:
    """
    Returns True if user has any activities
    """
    return len(get_activities_ids_impl(user=userId, limit=1)) > 0


def get_public_platform_by_id(platformId: int) -> PublicPlatformModelV2 | None:
    pf = Platform_or_none(platformId)
    if not pf:
        return None
    return pf.get_api_v2_model()


def get_public_game_by_id(gameId: int) -> PublicGameModelV2 | None:
    g = Game_or_none(gameId)
    if not g:
        return None
    return g.get_api_v2_model()


def get_public_user_by_id(userId: int) -> PublicUserModelV2 | None:
    user = User_or_none(userId)
    if not user:
        return None
    return user.get_api_v2_model()


def get_public_activity_by_id(activityId: int) -> PublicActivityModelV2 | None:
    activity = Activity_or_none(activityId)
    if not activity:
        return None
    return activity.get_api_v2_model()


######################## API ENDPOINTS ############################

####################
# Users
####################


@router.get("/users", tags=["users"], response_model=list[UserStatsV2])
def get_users(
    offset=0,
    limit=25,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> list[UserStatsV2]:
    """
    Get summarized users. Can also filter by gameId and platformId, and set a before/after timestamp to get a range.
    """
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

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
    return data


@router.get("/user/{userId}", tags=["users"], response_model=UserStatsV2)
def get_user(
    userId: int,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
    platformId: int | None = None,
) -> UserStatsV2:
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
    assert first_activity and latest_activity

    oldest_id = first_activity.id
    newest_id = latest_activity.id

    return UserStatsV2(
        id=user.id,
        name=user.name,
        discord_id=user.discord_id,
        default_platform_id=user.default_platform_id,
        created=user.created,
        updated=user.updated,
        playtime_secs=totals.playtime_secs,
        activity_count=totals.activity_count,
        game_count=totals.game_count,
        platform_count=totals.platform_count,
        oldest_activity_id=oldest_id,
        newest_activity_id=newest_id,
    )


#################
# Activities
#################


@router.get(
    "/activities", tags=["activities"], response_model=list[PublicActivityModelV2]
)
def get_activities(
    offset=0,
    limit=25,
    order: Literal["desc", "asc"] = "desc",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> list[PublicActivityModelV2]:
    return get_activities_impl(
        offset=offset,
        limit=limit,
        order=order,
        user=user,
        game=game,
        platform=platform,
        before=before,
        after=after,
        include_game_children=include_game_children,
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
    include_game_children=False,
) -> list[PublicActivityModelV2]:
    limit = clamp(limit, 1, 500)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

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
        g = Game_or_none(game)
        if g:
            game_ids = [g.get_id()]
            if include_game_children:
                for child in g.get_children():
                    game_ids.append(child.get_id())
            filters.append(Activity.game.in_(game_ids))  # type: ignore
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

    data = []
    for a in query:
        data.append(cast(Activity, a).get_api_v2_model())

    return data


def get_activities_ids_impl(
    offset=0,
    limit=25,
    order: Literal["desc", "asc"] = "desc",
    user: int | None = None,
    game: int | None = None,
    platform: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children=False,
) -> list[int]:
    limit = clamp(limit, 1, 500)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

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
        g = Game_or_none(game)
        if g:
            game_ids = [g.get_id()]
            if include_game_children:
                for child in g.get_children():
                    game_ids.append(child.get_id())
            filters.append(Activity.game.in_(game_ids))  # type: ignore
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

    data = []
    for a in query:
        data.append(a.get_id())
    return data


@router.get(
    "/activity/newest", tags=["activities"], response_model=PublicActivityModelV2
)
def get_newest_activity(
    userid: int | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> PublicActivityModelV2 | None:
    id = get_oldest_or_newest_activity_id(
        oldest=False,
        userid=userid,
        gameid=gameid,
        platformid=platformid,
        before=before,
        after=after,
        include_game_children=include_game_children,
    )
    if id:
        return get_public_activity_by_id(id)
    return None


@router.get(
    "/activity/oldest", tags=["activities"], response_model=PublicActivityModelV2
)
def get_oldest_activity(
    userid: int | None = None,
    gameid: int | None = None,
    platformid: int | None = None,
    before: int | None = None,
    after: int | None = None,
    include_game_children: bool = False,
) -> PublicActivityModelV2 | None:
    id = get_oldest_or_newest_activity_id(
        oldest=True,
        userid=userid,
        gameid=gameid,
        platformid=platformid,
        before=before,
        after=after,
        include_game_children=include_game_children,
    )
    if id:
        return get_public_activity_by_id(id)
    return None


@router.get(
    "/activity/{activity_id}",
    tags=["activities"],
    response_model=PublicActivityModelV2,
    description="Get a single activity by ID. Returns 404 if not found.",
)
def get_activity(activity_id: int) -> PublicActivityModelV2 | None:
    a = get_public_activity_by_id(activity_id)
    if a:
        return get_public_activity_by_id(activity_id)
    return not_found("Activity not found")


@router.get(
    "/activities/{activity_ids}",
    tags=["activities"],
    response_model=list[PublicActivityModelV2],
    description="Get multiple activities by ID (comma separated)",
)
def get_activities_csv(activity_ids: str) -> list[PublicActivityModelV2]:
    activities = []
    for activity_id in activity_ids.split(","):
        a = get_public_activity_by_id(int(activity_id))
        if a:
            activities.append(a)
    return activities


##############
# Games
#############


@router.get("/games", tags=["games"], response_model=list[GameStatsV2])
def get_games(
    offset=0,
    limit=25,
    userId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    search: str | None = None,
) -> list[GameStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    filters = ACTIVITY_BASE_FILTERS.copy()
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

    data = []

    if search:
        if len(search) < 2:
            return bad_request("Search query must be at least 2 characters long")
        # TODO: Get rid of total here, no longer needed
        results, total = search_games_for_api(
            query=search,
            limit=limit,
            offset=offset,
            userId=userId,
            platformId=platformId,
        )
        for r in results:
            try:
                gameWithStats = get_game(
                    userId=userId,
                    gameId=r.get_id(),
                    platformId=platformId,
                    before=before,
                    after=after,
                )
                data.append(gameWithStats)
            except Exception as e:
                logger.warning("Skipping game %s in get_games: %s", r.get_id(), e)
    else:
        # only return games with activity
        query = Activity.select().where(*filters)
        query = query.order_by(Activity.game.asc()).distinct(Activity.game)
        activities = query[offset : offset + limit]  # type: ignore
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
    return data


@router.get("/game/{gameId}", tags=["games"], response_model=GameStatsV2)
def get_game(
    gameId: int,
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    platformId: int | None = None,
) -> GameStatsV2:
    game = Game_or_none(gameId)
    if not game:
        return not_found("Game not found")

    gameModel = game.get_api_v2_model()

    totals_incl_children = get_totals(
        userId=userId,
        gameId=game.get_id(),
        before=before,
        after=after,
        platformId=platformId,
        include_game_children=True,
    )

    totals_excl_children = get_totals(
        userId=userId,
        gameId=game.get_id(),
        before=before,
        after=after,
        platformId=platformId,
        include_game_children=False,
    )

    oldest_activivity_id = get_oldest_or_newest_activity_id(
        oldest=True,
        userid=userId,
        gameid=game.get_id(),
        before=before,
        after=after,
        platformid=platformId,
        include_game_children=True,
    )

    newest_activity_id = get_oldest_or_newest_activity_id(
        oldest=False,
        userid=userId,
        gameid=game.get_id(),
        before=before,
        after=after,
        platformid=platformId,
        include_game_children=True,
    )

    return GameStatsV2(
        id=gameModel.id,
        name=gameModel.name,
        steam_id=gameModel.steam_id,
        sgdb_id=gameModel.sgdb_id,
        image_url=gameModel.image_url,
        aliases=gameModel.aliases,
        release_year=gameModel.release_year,
        created=gameModel.created,
        updated=gameModel.updated,
        children_ids=gameModel.children_ids,
        parent_id=gameModel.parent_id,
        playtime_secs=totals_incl_children.playtime_secs,
        activity_count=totals_incl_children.activity_count,
        user_count=totals_incl_children.user_count,
        platform_count=totals_incl_children.platform_count,
        playtime_secs_excl_children=totals_excl_children.playtime_secs,
        activity_count_excl_children=totals_excl_children.activity_count,
        oldest_activity_id=oldest_activivity_id,
        newest_activity_id=newest_activity_id,
    )


##############
# Platforms
##############


@router.get(
    "/platforms",
    tags=["platforms"],
    response_model=list[PlatformStatsV2],
)
def get_platforms(
    offset=0,
    limit=25,
    userId: int | None = None,
    gameId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> list[PlatformStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    filters = ACTIVITY_BASE_FILTERS.copy()
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

    query = Activity.select().where(*filters)
    query = query.order_by(Activity.platform.asc()).distinct(Activity.platform)
    activities = query[offset : offset + limit]  # type: ignore

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
    return data


@router.get(
    "/platform/{platformId}",
    tags=["platforms"],
    response_model=PlatformStatsV2,
)
def get_platform(
    platformId: int,
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
) -> PlatformStatsV2:
    platformModel = get_public_platform_by_id(platformId)
    if not platformModel:
        return not_found("Platform not found")

    platform_totals = get_platform(
        platformId=platformId, userId=userId, before=before, after=after, gameId=gameId
    )

    oldest_activity_id = get_oldest_or_newest_activity_id(
        oldest=True,
        userid=userId,
        gameid=gameId,
        before=before,
        after=after,
        platformid=platformId,
    )
    newest_activity_id = get_oldest_or_newest_activity_id(
        oldest=False,
        userid=userId,
        gameid=gameId,
        before=before,
        after=after,
        platformid=platformId,
    )

    return PlatformStatsV2(
        id=platformModel.id,
        name=platformModel.name,
        created=platformModel.created,
        updated=platformModel.updated,
        icon=platformModel.icon,
        playtime_secs=platform_totals.playtime_secs,
        activity_count=platform_totals.activity_count,
        game_count=platform_totals.game_count,
        user_count=platform_totals.user_count,
        abbreviation=platformModel.abbreviation,
        color_primary=platformModel.color_primary,
        color_secondary=platformModel.color_secondary,
        oldest_activity_id=oldest_activity_id,
        newest_activity_id=newest_activity_id,
    )
