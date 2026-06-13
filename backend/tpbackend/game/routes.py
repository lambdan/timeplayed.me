from tpbackend.activity.query import ActivityQuery
from tpbackend.game.models import API_GameWithStats
from tpbackend.game.query import GameStatsQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.game.query import GameQuery
from tpbackend.game.models import API_Game
from tpbackend.api.responses import bad_request, not_found
import logging
from fastapi import APIRouter, Path
from tpbackend.common.types import (
    QUERY_TS_BEFORE,
    QUERY_TS_AFTER,
    AscDescOrder,
)

logger = logging.getLogger("games-routes")
router = APIRouter()


def __get_games_stats(
    gids: list[int] | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user_id: int | None = None,
    platform_id: int | None = None,
    sort: GameStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
) -> list[API_GameWithStats]:
    bf = parseTS(before)
    af = parseTS(after)

    query = GameStatsQuery.base()
    if gids and len(gids) > 0:
        if len(gids) > 100:
            return bad_request("Cannot request more than 100 games at once")
        query = GameStatsQuery.apply_ids(query, gids)

    if bf:
        query = ActivityQuery.before(query, bf)

    if af:
        query = ActivityQuery.after(query, af)

    if user_id:
        query = ActivityQuery.user(query, user_id)

    if platform_id:
        query = ActivityQuery.platform(query, platform_id)

    if search:
        query = GameQuery.search(query, search)

    query = GameStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, int(offset)))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    return [API_GameWithStats.from_game(game) for game in query]


@router.get(
    "/game-stats/{game_id}",
    tags=["games", "stats"],
    response_model=API_GameWithStats,
)
def get_single_game_stats(
    game_id: int,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    platform: int | None = None,
) -> API_GameWithStats:
    x = __get_games_stats(
        gids=[int(game_id)],
        before=before,
        after=after,
        user_id=user,
        platform_id=platform,
    )
    if len(x) == 0:
        return not_found("Game not found")
    return x[0]


@router.get(
    "/games-stats/{game_ids}",
    response_model=list[API_GameWithStats],
    tags=["games", "stats"],
)
def get_many_games_stats(
    game_ids: str = Path(description="Comma-separated list of game IDs"),
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    platform: int | None = None,
    sort: GameStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_GameWithStats]:
    gids = parse_csv(game_ids)
    return __get_games_stats(
        gids=gids,
        before=before,
        after=after,
        user_id=user,
        platform_id=platform,
        sort=sort,
        order=order,
    )


@router.get(
    "/games-stats",
    tags=["games", "stats"],
    response_model=list[API_GameWithStats],
)
def get_games_stats(
    offset=0,
    limit=25,
    user: int | None = None,
    platform: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    sort: GameStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
    search="",
) -> list[API_GameWithStats]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_games_stats(
        before=before,
        after=after,
        user_id=user,
        platform_id=platform,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
        search=search,
    )


################################################
############# plain game (no stats) ############
################################################


def __get_games(
    ids: list[int] | None = None,
    sort: GameQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
) -> list[API_Game]:
    query = GameQuery.base()
    if ids and len(ids) > 0:
        query = GameQuery.apply_ids(query=query, game_ids=ids)

    if search:
        query = GameQuery.search(query=query, search=search)

    query = GameQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, int(offset)))
    if limit:
        query = query.limit(clamp(limit, 1, 100))
    return [API_Game.from_game(g) for g in query]


@router.get(
    "/game/{game_id}",
    tags=["games"],
    response_model=API_Game,
)
def get_single_game(game_id: int) -> API_Game:
    x = __get_games(ids=[int(game_id)])
    if len(x) == 0:
        return not_found("Game not found")
    return x[0]


@router.get(
    "/games/{game_ids}",
    tags=["games"],
    response_model=list[API_Game],
)
def get_many_games(
    game_ids: str = Path(description="Comma-separated list of game IDs"),
    sort: GameQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[API_Game]:
    gids = parse_csv(game_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 games at once")
    return __get_games(
        ids=gids,
        sort=sort,
        order=order,
    )


@router.get(
    "/games",
    tags=["games"],
    response_model=list[API_Game],
)
def get_games(
    offset=0,
    limit=25,
    sort: GameQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
    search="",
) -> list[API_Game]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_games(
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
