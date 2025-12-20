import os
import logging
from pydantic import BaseModel
from steamgrid import SteamGridDB
from steamgrid import StyleType, MimeType
from steamgrid.http import HTTPException
import redis
import json

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_CLIENT = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
REDIS_EXP = 86400  # 1 day


logger = logging.getLogger("SteamGridDB")
ONE_DAY = 24 * 60 * 60  # seconds
sgdb = SteamGridDB(os.environ["SGDB_TOKEN"])


class SGDB_Game(BaseModel):
    id: int
    name: str
    verified: bool
    release_date: float


class SGDB_Author(BaseModel):
    name: str | None
    steam64: str | None
    avatar: str | None


class SGDB_Grid(BaseModel):
    id: int | None
    score: int | None
    width: int | None
    height: int | None
    style: str | None
    mime: str | None
    language: str | None
    url: str | None
    thumb: str | None
    type: str | None
    author: SGDB_Author | None
    upvotes: int | None
    downvotes: int | None


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

    key = f"6sgdb_search_{query}"

    redisCache = REDIS_CLIENT.get(key)
    if redisCache:
        logger.info("Search was cached for query %s", query)
        decoded = redisCache.decode("utf-8")  # type: ignore
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
    REDIS_CLIENT.setex(key, REDIS_EXP, jsonEncode(res))
    return res


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

    key = f"2sgdb_grids_{game_id}"
    cached = REDIS_CLIENT.get(key)
    if cached:
        logger.info("Grids were cached for game ID %d", game_id)
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
    except HTTPException as e:
        logger.error("HTTPException when fetching grids for game ID %d", game_id, e)
        pass

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

    REDIS_CLIENT.setex(key, REDIS_EXP, jsonEncode(gs))
    return gs


def get_best_grid(game_id: int) -> SGDB_Grid | None:
    grids = get_grids(game_id)
    if not grids:
        return None

    bestScore = 0
    bestGrid = None
    for grid in grids:
        thisScore = 0

        if grid.style == StyleType.Alternate:
            thisScore += 10

        if grid.language == "en":
            thisScore += 1

        if grid.width == 600 and grid.height == 900:
            thisScore += 1

        thisScore += grid.upvotes or 0
        thisScore -= grid.downvotes or 0

        if thisScore > bestScore:
            bestScore = thisScore
            bestGrid = grid

    return bestGrid
