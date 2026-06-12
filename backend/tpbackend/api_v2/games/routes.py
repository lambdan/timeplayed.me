from tpbackend.api_v2.activities.query import ActivityQuery
from tpbackend.api_v2.games.models import GameStatsV2
from tpbackend.api_v2.games.query import GameStatsQuery
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.api_v2.games.query import GameQuery
from tpbackend.api_v2.games.models import PublicGameModelV2
from tpbackend.api_v2.responses import bad_request, not_found
import logging
from fastapi import APIRouter, Path
from tpbackend.api_v2.types import (
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
) -> list[GameStatsV2]:
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

    query = GameStatsQuery.apply_sort(query, sort, order)

    if offset:
        query = query.offset(max(0, offset))

    if limit:
        query = query.limit(clamp(limit, 1, 100))

    # print("__get_users_stats QUERY", query.sql())
    return [GameStatsV2.from_game(game) for game in query]


@router.get(
    "/game-stats/{game_id}",
    tags=["games", "stats"],
    response_model=GameStatsV2,
)
def get_game_stats(
    game_id: int,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    platform: int | None = None,
) -> GameStatsV2:
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
    response_model=list[GameStatsV2],
    tags=["games", "stats"],
    description="Get many games, including stats, by id (comma separated). Max 100 at once.",
)
def get_games_stats(
    game_ids: str,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    user: int | None = None,
    platform: int | None = None,
    sort: GameStatsQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[GameStatsV2]:
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


@router.get("/games-stats", tags=["games", "stats"], response_model=list[GameStatsV2])
def get_all_games_stats(
    offset=0,
    limit=25,
    user: int | None = None,
    platform: int | None = None,
    before: int | None = QUERY_TS_BEFORE,
    after: int | None = QUERY_TS_AFTER,
    sort: GameStatsQuery.SORTS_LITERAL = "playtime",
    order: AscDescOrder = "desc",
) -> list[GameStatsV2]:
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
) -> list[PublicGameModelV2]:
    query = GameQuery.base()
    if ids and len(ids) > 0:
        query = GameQuery.apply_ids(query=query, game_ids=ids)
    query = GameQuery.apply_sort(query=query, sort=sort, order=order)

    if offset:
        query = query.offset(max(0, offset))
    if limit:
        query = query.limit(clamp(limit, 1, 100))
    return [PublicGameModelV2.from_game(g) for g in query]


@router.get("/game/{game_id}", tags=["games"], response_model=PublicGameModelV2)
def get_game_by_id(game_id: int) -> PublicGameModelV2:
    x = __get_games(ids=[int(game_id)])
    if len(x) == 0:
        return not_found("Game not found")
    return x[0]


@router.get(
    "/games/{game_ids}",
    tags=["games"],
    response_model=list[PublicGameModelV2],
    description="Get many games by id (comma separated). Max 100 at once.",
)
def get_games_by_ids(
    game_ids: str,
    sort: GameQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicGameModelV2]:
    gids = parse_csv(game_ids)
    if len(gids) > 100:
        return bad_request("Cannot request more than 100 games at once")
    return __get_games(
        ids=gids,
        sort=sort,
        order=order,
    )


@router.get("/games", tags=["games"], response_model=list[PublicGameModelV2])
def get_all_games(
    offset=0,
    limit=25,
    sort: GameQuery.SORTS_LITERAL = "id",
    order: AscDescOrder = "asc",
) -> list[PublicGameModelV2]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_games(
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
    )
