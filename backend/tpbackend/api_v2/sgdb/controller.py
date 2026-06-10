from steamgrid import Game, SteamGridDB
from steamgrid import StyleType, MimeType
import json
import os
from tpbackend.api_v2.sgdb.models import SGDB_Game, SGDB_Grid, SGDB_Author
from tpbackend.cache import cache_get, cache_set
import logging

logger = logging.getLogger("sgdb")

sgdb = SteamGridDB(os.environ["SGDB_TOKEN"])
ONE_DAY = 60 * 60 * 24

__PREFERED_ASPECT = 600 / 900


def search(query: str) -> list[SGDB_Game]:
    def jsonEncode(val: list[SGDB_Game]) -> str:
        res = []
        for v in val:
            res.append(v.model_dump())
        return json.dumps(res, ensure_ascii=False)

    def jsonDecode(val: str) -> list[SGDB_Game]:
        res = []
        for v in json.loads(val):
            # res.append(v)
            res.append(SGDB_Game.model_validate(v))
        return res

    key = f"sgdb_search:{query}"

    cached = cache_get(key)
    if cached:
        decoded = cached.decode("utf-8")  # type: ignore
        return jsonDecode(decoded)

    s = sgdb.search_game(query)
    res = []
    if s:
        for game in s:
            if game.id and game.name and game.release_date:
                res.append(
                    SGDB_Game(
                        id=game.id,
                        name=game.name,
                        verified=bool(game.verified is not None and game.verified),
                        release_date=game.release_date.timestamp(),
                    )
                )
    cache_set(key, jsonEncode(res), ex=ONE_DAY)
    return res


def get_game_by_id(game_id: int) -> Game | None:
    try:
        g = sgdb.get_game_by_gameid(game_id)
        if g and g.id == game_id:
            return g
    except Exception as e:
        logger.error("HTTPException when fetching game for game ID %d", game_id, e)
    return None


def get_grids(game_id: int) -> list[SGDB_Grid]:

    def jsonEncode(val: list[SGDB_Grid]) -> str:
        res = []
        for v in val:
            res.append(v.model_dump())
        return json.dumps(res, ensure_ascii=False)

    def jsonDecode(val: str) -> list[SGDB_Grid]:
        res = []
        for v in json.loads(val):
            res.append(SGDB_Grid.model_validate(v))
        return res

    key = f"sgdb_grids:{game_id}"
    cached = cache_get(key)
    if cached:
        decoded = cached.decode("utf-8")  # type: ignore
        return jsonDecode(decoded)

    logger.info("Fetching grids for game ID %d from SteamGridDB", game_id)
    fetch = None
    try:
        fetch = sgdb.get_grids_by_gameid(
            game_ids=[game_id],
            styles=[StyleType.Alternate],
            mimes=[MimeType.PNG, MimeType.JPEG, MimeType.WEBP],
            is_nsfw=False,
        )
    except Exception as e:
        logger.error("Exception when fetching grids for game ID %d", game_id, e)
        return []

    gs = []
    if fetch:
        for g in fetch:
            author = SGDB_Author(
                name=getattr(g.author, "name", None),
                steam64=getattr(g.author, "steam64", None),
                avatar=getattr(g.author, "avatar", None),
            )
            full_url = getattr(g, "url", None)
            thumb_url = getattr(g, "thumb", full_url)  # use full if thumb not available
            new_grid: SGDB_Grid = SGDB_Grid(
                url=full_url,
                thumb=thumb_url,
                id=getattr(g, "id", None),
                score=getattr(g, "score", None),
                width=getattr(g, "width", None),
                height=getattr(g, "height", None),
                style=getattr(g, "style", None),
                mime=getattr(g, "mime", None),
                language=getattr(g, "language", None),
                upvotes=getattr(g, "upvotes", None),
                downvotes=getattr(g, "downvotes", None),
                author=author,
                type=getattr(g, "type", None),
            )
            gs.append(new_grid)

    cache_set(key, jsonEncode(gs), ex=ONE_DAY)
    return gs


def get_best_grid(game_id: int) -> SGDB_Grid | None:
    grids = get_grids(game_id)
    if not grids:
        return None

    best_score = 0
    best_grid = None
    best_lang = None
    for grid in grids:
        w = grid.width or 1
        h = grid.height or 1
        if not w or not h:
            continue

        # prefer correct aspect
        if abs((w / h) - __PREFERED_ASPECT) > 0.1:
            continue

        # prefer english, but if no english available, allow other languages
        lang = grid.language
        if best_lang == "en" and lang != "en":
            continue

        score = grid.score or 0
        score += grid.upvotes or 0
        score -= grid.downvotes or 0
        if score > best_score or best_grid is None:
            best_score = score
            best_grid = grid
            best_lang = lang

    return best_grid
