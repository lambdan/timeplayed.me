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
    search_games,
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
    Platform,
    Game,
    User,
)
from tpbackend.api_responses import bad_request
from tpbackend.api import get_totals
import logging

from fastapi import APIRouter

logger = logging.getLogger("api_v2")
router = APIRouter()


ACTIVITY_BASE_FILTERS = [Activity.hidden == False]  # noqa: E712


################ HELPERS ##################


def parse_csv(input: int | str) -> list[int]:
    def ret(v):
        logger.info("parse_csv: '%s' -> %s", input, v)
        return v

    if isinstance(input, int):
        return ret([input])
    res = []
    input = input.replace("%2C", ",")  # replace url encoded
    for part in input.split(","):
        try:
            res.append(int(part))
        except Exception:
            continue
    return ret(res)


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


@router.get(
    "/users/{user_ids}/stats", tags=["users", "stats"], response_model=list[UserStatsV2]
)
def get_users_stats(
    user_ids: int | str,
    before: int | None = None,
    after: int | None = None,
    game_id: int | None = None,
    platform_id: int | None = None,
) -> list[UserStatsV2]:
    uids = parse_csv(user_ids)
    if len(uids) > 100:
        return bad_request("Cannot request more than 100 users at once")

    res = []
    for userId in uids:
        user = get_public_user_by_id(userId)
        if not user or not user_has_activities(userId):
            continue

        totals = get_totals(
            userId=userId,
            gameId=game_id,
            platformId=platform_id,
            before=before,
            after=after,
        )

        res.append(
            UserStatsV2(
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
            )
        )
    return res


@router.get("/users/stats", tags=["users", "stats"], response_model=list[UserStatsV2])
def get_all_users_stats(
    offset=0,
    limit=25,
    gameId: int | None = None,
    platformId: int | None = None,
    before: int | None = None,
    after: int | None = None,
) -> list[UserStatsV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)
    before, after = validateTS(before), validateTS(after)

    all_users = User.select().order_by(User.id.asc()).offset(offset).limit(limit)
    ids = ",".join(str(u.id) for u in all_users)
    return get_users_stats(
        ids, game_id=gameId, platform_id=platformId, before=before, after=after
    )


@router.get("/users/{ids}", tags=["users"], response_model=list[PublicUserModelV2])
def get_users(ids: int | str) -> list[PublicUserModelV2]:
    gids = parse_csv(ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 users at once")
    res = []
    for gid in gids:
        g = get_public_user_by_id(gid)
        if g:
            res.append(g)
    return res


@router.get("/users", tags=["users"], response_model=list[PublicUserModelV2])
def get_all_users(
    offset=0,
    limit=25,
) -> list[PublicUserModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    res = []
    raw = User.select().order_by(User.id.asc()).offset(offset).limit(limit)
    for u in raw:
        res.append(cast(User, u).get_api_v2_model())
    return res


#################
# Activities
#################


@router.get(
    "/activities", tags=["activities"], response_model=list[PublicActivityModelV2]
)
def get_all_activities(
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
    "/activities/{activity_ids}",
    tags=["activities"],
    response_model=list[PublicActivityModelV2],
)
def get_activities(activity_ids: str | int) -> list[PublicActivityModelV2]:
    aids = parse_csv(activity_ids)  # haha
    if len(aids) > 100:
        return bad_request("Cannot request more than 100 activities at once")
    res = []
    for aid in aids:
        a = get_public_activity_by_id(aid)
        if a:
            res.append(a)
    return res


##############
# Games
#############


@router.get("/games", tags=["games"], response_model=list[PublicGameModelV2])
def get_all_games(
    offset=0,
    limit=25,
    search: str | None = None,
    userId: int | None = None,
    platformId: int | None = None,
) -> list[PublicGameModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    res = []
    raw = []
    if search:
        if len(search) < 2:
            return bad_request("Search query must be at least 2 characters long")
        raw = search_games(
            query=search,
            limit=limit,
            offset=offset,
            userId=userId,
            platformId=platformId,
        )
    else:
        raw = Game.select().order_by(Game.id.asc()).offset(offset).limit(limit)
    for g in raw:
        res.append(cast(Game, g).get_api_v2_model())
    return res


@router.get("/games/stats", tags=["games", "stats"], response_model=list[GameStatsV2])
def get_all_games_stats(
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

    gids = []

    if search:
        if len(search) < 2:
            return bad_request("Search query must be at least 2 characters long")
        results = search_games(
            query=search,
            limit=limit,
            offset=offset,
            userId=userId,
            platformId=platformId,
        )
        for r in results:
            gids.append(r.get_id())
    else:
        all_games = Game.select().order_by(Game.id.asc()).offset(offset).limit(limit)
        for g in all_games:
            gids.append(g.id)
    gids_str = ",".join(str(gid) for gid in gids)
    return get_games_stats(
        gids_str, userId=userId, platformId=platformId, before=before, after=after
    )


@router.get(
    "/games/{game_ids}/stats",
    tags=["games", "stats"],
    response_model=list[GameStatsV2],
)
def get_games_stats(
    game_ids: int | str,
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    platformId: int | None = None,
) -> list[GameStatsV2]:
    gids = parse_csv(game_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 games at once")

    res = []
    for gameId in gids:
        game = Game_or_none(gameId)
        if not game:
            continue

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

        res.append(
            GameStatsV2(
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
            )
        )
    return res


@router.get("/games/{ids}", tags=["games"], response_model=list[PublicGameModelV2])
def get_games(ids: int | str) -> list[PublicGameModelV2]:
    logger.info("HIT /games/ids")
    gids = parse_csv(ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 games at once")
    res = []
    for gid in gids:
        g = get_public_game_by_id(gid)
        if g:
            res.append(g)
    return res


##############
# Platforms
##############


@router.get(
    "/platforms/{platform_ids}/stats",
    tags=["platforms"],
    response_model=list[PlatformStatsV2],
)
def get_platforms_stats(
    platform_ids: int | str,
    userId: int | None = None,
    before: int | None = None,
    after: int | None = None,
    gameId: int | None = None,
) -> list[PlatformStatsV2]:
    res = []
    pids = parse_csv(platform_ids)
    if len(pids) > 100:
        return bad_request("Cannot request more than 100 platforms at once")

    for platformId in pids:
        platformModel = get_public_platform_by_id(platformId)
        if not platformModel:
            continue

        platform_totals = get_totals(
            userId=userId,
            gameId=gameId,
            platformId=platformId,
            before=before,
            after=after,
        )

        res.append(
            PlatformStatsV2(
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
            )
        )
    return res


@router.get(
    "/platforms/stats",
    tags=["platforms", "stats"],
    response_model=list[PlatformStatsV2],
)
def get_all_platforms_stats(
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

    all_platforms = (
        Platform.select().order_by(Platform.id.asc()).offset(offset).limit(limit)
    )
    ids = ",".join(str(p.id) for p in all_platforms)
    return get_platforms_stats(
        ids, userId=userId, gameId=gameId, before=before, after=after
    )


@router.get(
    "/platforms/{ids}", tags=["platforms"], response_model=list[PublicPlatformModelV2]
)
def get_platforms(ids: int | str) -> list[PublicPlatformModelV2]:
    pids = parse_csv(ids)
    if len(pids) > 100:
        return bad_request("Cannot request more than 100 platforms at once")
    res = []
    for pid in pids:
        p = get_public_platform_by_id(pid)
        if p:
            res.append(p)
    return res


@router.get(
    "/platforms", tags=["platforms"], response_model=list[PublicPlatformModelV2]
)
def get_all_platforms(
    offset=0,
    limit=25,
) -> list[PublicPlatformModelV2]:
    limit = clamp(limit, 1, 100)
    offset = max(0, offset)

    res = []
    raw = Platform.select().order_by(Platform.id.asc()).offset(offset).limit(limit)
    for p in raw:
        res.append(cast(Platform, p).get_api_v2_model())
    return res
