from fastapi.responses import RedirectResponse
from tpbackend.activity.query import ActivityQuery
from tpbackend.game.models import API_GameWithStats
from tpbackend.game.query import GameStatsQuery
from tpbackend.igdb.controller import get_or_create_game
from tpbackend.igdb.controller import enabled as igdb_enabled
from tpbackend.igdb.controller import search_game as igdb_search_game
from tpbackend.igdb.models import IGDB_SearchResult
from tpbackend.api.auth import ManualActivityUser
from tpbackend.utils2 import clamp, parseTS, parse_csv
from tpbackend.game.query import GameQuery
from tpbackend.game.models import (
    API_CoverImage,
    API_Game,
    API_GameCover,
    CoverVersion,
)
from tpbackend.game.cover import find_cover
from tpbackend.files.images import public_url
from tpbackend.game.select import GameSelect
from tpbackend.api.responses import bad_request, not_found, service_unavailable
import logging
from fastapi import APIRouter, Path, Query
from tpbackend.api.params import (
    AscDescOrder,
    offset,
    limit,
    path_csv,
    path_id,
    query_id,
    query_ts,
    sorts,
    query_search,
    query_include_children,
    query_platform_include_children,
)

logger = logging.getLogger("games-routes")
router = APIRouter()


def __get_games_stats(
    gids: list[int] | None = None,
    before: int | None = None,
    after: int | None = None,
    user_id: int | None = None,
    platform_id: int | None = None,
    include_child_platforms=False,
    sort="id",
    order="asc",
    offset: int | None = None,
    limit: int | None = None,
    search="",
    include_children=False,
    only_top_level=False,
) -> list[API_GameWithStats]:
    bf = parseTS(before)
    af = parseTS(after)

    if include_children:
        query = GameStatsQuery.base_with_children()
    else:
        query = GameStatsQuery.base()

    if only_top_level:
        query = GameStatsQuery.top_level(query)

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
        query = ActivityQuery.platform(query, platform_id, include_child_platforms)

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
    game_id=path_id("game"),
    before=query_ts("before"),
    after=query_ts("after"),
    user=query_id("user"),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
    include_children: bool = query_include_children(),
) -> API_GameWithStats:
    x = __get_games_stats(
        gids=[int(game_id)],
        before=before,
        after=after,
        user_id=user,
        platform_id=platform,
        include_child_platforms=include_child_platforms,
        include_children=include_children,
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
    game_ids=path_csv("game ids"),
    before=query_ts("before"),
    after=query_ts("after"),
    user=query_id("user"),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
    sort=sorts(list(GameStatsQuery.SORTS.keys()), default="id"),
    order: AscDescOrder = "asc",
    include_children: bool = query_include_children(),
) -> list[API_GameWithStats]:
    gids = parse_csv(game_ids)
    return __get_games_stats(
        gids=gids,
        before=before,
        after=after,
        user_id=user,
        platform_id=platform,
        include_child_platforms=include_child_platforms,
        sort=sort,
        order=order,
        include_children=include_children,
    )


@router.get(
    "/games-stats",
    tags=["games", "stats"],
    response_model=list[API_GameWithStats],
)
def get_games_stats(
    offset=offset(),
    limit=limit(),
    user=query_id("user"),
    platform=query_id("platform"),
    include_child_platforms: bool = query_platform_include_children(),
    before=query_ts("before"),
    after=query_ts("after"),
    sort=sorts(list(GameStatsQuery.SORTS.keys()), default="playtime"),
    order: AscDescOrder = "desc",
    search=query_search("games"),
    include_children: bool = query_include_children(
        "Include the playtime of child games (at any depth) in their parent. "
        "Children are then not listed separately, only games without a parent are."
    ),
) -> list[API_GameWithStats]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_games_stats(
        before=before,
        after=after,
        user_id=user,
        platform_id=platform,
        include_child_platforms=include_child_platforms,
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
        search=search,
        include_children=include_children,
        # children are counted in their parent
        only_top_level=include_children,
    )


################################################
############# plain game (no stats) ############
################################################


def __get_games(
    ids: list[int] | None = None,
    sort="id",
    order="asc",
    offset: int | None = None,
    limit: int | None = None,
    search=None,
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
def get_single_game(game_id=path_id("game")) -> API_Game:
    x = __get_games(ids=[int(game_id)])
    if len(x) == 0:
        return not_found("Game not found")
    return x[0]


@router.get(
    "/game/{game_id}/cover",
    tags=["games"],
    response_model=API_GameCover,
    description="What's available of a game's cover art (uploaded by an admin, or from IGDB): "
    "its versions, and where it's from. "
    "NSFW covers are given to everyone, the site decides whether to show them",
)
def get_game_cover(game_id=path_id("game")) -> API_GameCover:
    game = GameSelect.by_id(int(game_id))
    if not game:
        return not_found("Game not found")
    cover = find_cover(game)
    return API_GameCover(
        source=cover.source,
        credits=cover.credits,
        versions={
            name: API_CoverImage.from_image(image)
            for name, image in cover.versions.items()
        },
    )


@router.get(
    "/game/{game_id}/cover/{version}",
    tags=["games"],
    response_class=RedirectResponse,
    status_code=302,
    description="Redirects to that version of the cover (see /game/{game_id}/cover). "
    "404 if the game has no cover (or it's disabled). "
    "NSFW covers are given to everyone, the site decides whether to show them",
)
def get_game_cover_image(
    version: CoverVersion,
    game_id=path_id("game"),
):
    game = GameSelect.by_id(int(game_id))
    if not game:
        return not_found("Game not found")
    image = find_cover(game).versions.get(version)
    if not image:
        return not_found("Game has no cover")
    # short, so a new cover shows up soon. The file itself is cached for good
    return RedirectResponse(
        public_url(image),
        status_code=302,
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get(
    "/game_igdb/{igdb_id}",
    tags=["games", "IGDB"],
    response_model=API_Game,
    description="Get a game by its IGDB ID. If the game is not in the database, it will be created from IGDB data.",
)
def get_single_game_by_igdb_id(igdb_id=path_id("IGDB game")) -> API_Game:
    x = get_or_create_game(igdb_id, "Created by IGDB ID redirect")
    if x:
        return API_Game.from_game(x)
    if not igdb_enabled():
        return service_unavailable("Game not in database, and IGDB is not enabled")
    return not_found("Game not found (probably not in IGDB)")


@router.get(
    "/igdb/search",
    tags=["games", "IGDB"],
    response_model=list[IGDB_SearchResult],
    description="Search IGDB for games by name, for adding one that isn't here yet "
    "with /game_igdb/{igdb_id}. A number is also looked up as an IGDB ID, that game "
    "comes first. Needs the manual_activity permission",
)
def search_igdb(user: ManualActivityUser, q: str = Query()) -> list[IGDB_SearchResult]:
    if not igdb_enabled():
        return service_unavailable("IGDB is not enabled")
    return igdb_search_game(q)


@router.get(
    "/games/{game_ids}",
    tags=["games"],
    response_model=list[API_Game],
)
def get_many_games(
    game_ids=path_csv("game ids"),
    sort=sorts(list(GameQuery.SORTS.keys()), default="id"),
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
    offset=offset(),
    limit=limit(),
    sort=sorts(list(GameQuery.SORTS.keys()), default="id"),
    order: AscDescOrder = "asc",
    search=query_search("games"),
) -> list[API_Game]:
    limit = clamp(int(limit), 1, 100)
    offset = max(0, int(offset))

    return __get_games(
        sort=sort,
        order=order,
        offset=offset,
        limit=limit,
        search=search,
    )
