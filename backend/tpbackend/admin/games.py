import logging
from typing import Literal, cast

from fastapi import APIRouter, Query, Request
from fastapi.concurrency import run_in_threadpool

from tpbackend.admin.models import (
    Admin_Alias,
    Admin_Game,
    Admin_GameDetails,
    Admin_MergeGame,
    Admin_MergePreview,
    Admin_Moved,
    Admin_PatchGame,
    Admin_PostGame,
    Admin_SetIGDB,
    Admin_CoverUrl,
    activity_count,
    by_last_activity,
)
from tpbackend.api.auth import AdminUser
from tpbackend.api.params import limit, offset, query_search
from tpbackend.api.responses import bad_request, not_found, service_unavailable
from tpbackend.game.query import GameQuery
from tpbackend.game.select import GameSelect
from tpbackend.igdb import controller as igdb
from tpbackend.igdb.models import IGDB_GameInfo, IGDB_SearchResult
from tpbackend.operations import (
    adopt_name,
    merge_aliases,
    merge_games,
    sync_activities_hidden,
)
from tpbackend.files.images import get_image, get_versions, store_upload
from tpbackend.storage import Activity, Game, ImageFile, LiveActivity
from tpbackend.utils2 import clamp, ts_to_dt

logger = logging.getLogger("admin-games")
router = APIRouter()

# not_on_igdb: igdb id 0 and no cover, looked for on igdb but not there (yet)
Missing = Literal["igdb", "cover", "release_year", "activity", "not_on_igdb"]


def __get_game(game_id: int) -> Game:
    game = GameSelect.by_id(game_id)
    if not game:
        return not_found("Game not found")
    return game


def __is_missing(game: Game, missing: Missing) -> bool:
    if missing == "igdb":
        return game.get_igdb_id() is None
    if missing == "cover":
        # games not on igdb are left out, they're a list of their own
        return not game.has_cover_art() and game.igdb_id != 0
    if missing == "not_on_igdb":
        return game.igdb_id == 0 and not game.has_cover_art()
    if missing == "release_year":
        return game.get_release_year() is None
    return activity_count(game=game) == 0


def __check_name_and_year(game: Game, name: str, year: int | None):
    """two games with the same name and release year can't be told apart"""
    conflict = GameSelect.by_name_and_year(name, year)
    if conflict and conflict.get_id() != game.get_id():
        return bad_request(
            f"'{conflict.get_label()}' (id: {conflict.get_id()}) already has that name and release year"
        )


@router.get("/games", response_model=list[Admin_Game])
def get_games(
    offset=offset(),
    limit=limit(),
    search=query_search("games"),
    missing: Missing | None = None,
) -> list[Admin_Game]:
    offset = max(0, int(offset))
    limit = clamp(int(limit), 1, 100)
    query = GameQuery.base(include_hidden=True)
    query = GameQuery.search(query, search=search)
    query = by_last_activity(query, Game, Activity.game)
    if missing:
        # some of these are inherited from the parent, so filter in python
        games = [g for g in query if __is_missing(cast(Game, g), missing)]
        games = games[offset : offset + limit]
    else:
        games = query.offset(offset).limit(limit)
    return [Admin_Game.from_game(g) for g in games]


@router.post("/game", response_model=Admin_GameDetails)
def add_game(data: Admin_PostGame) -> Admin_GameDetails:
    name = data.name.strip()
    if not name:
        return bad_request("Name cannot be empty")
    existing = GameSelect.by_name_and_year(name, None)
    if existing:
        return bad_request(
            f"Game with that name and no release year already exists (id: {existing.get_id()})"
        )
    game = cast(Game, Game.create(name=name))
    game.add_history("Game added")
    game.save()
    return Admin_GameDetails.from_game(game)


@router.get("/game/{game_id}", response_model=Admin_GameDetails)
def get_game(game_id: int) -> Admin_GameDetails:
    return Admin_GameDetails.from_game(__get_game(game_id))


@router.patch("/game/{game_id}", response_model=Admin_GameDetails)
def patch_game(game_id: int, data: Admin_PatchGame) -> Admin_GameDetails:
    game = __get_game(game_id)
    sent = data.model_fields_set

    name = game.get_name()
    if "name" in sent:
        name = (data.name or "").strip()
        if not name:
            return bad_request("Name cannot be empty")
    year = game.get_release_year()
    if "release_year" in sent:
        year = data.release_year
    if name != game.get_name() or year != game.get_release_year():
        __check_name_and_year(game, name, year)
    if name != game.get_name():
        game.set_name(name)
    if year != game.get_release_year():
        game.set_release_year(year)

    if "cover_disabled" in sent:
        if data.cover_disabled is None:
            return bad_request("cover_disabled cannot be null")
        game.set_cover_disabled(data.cover_disabled)

    if "nsfw" in sent:
        if data.nsfw is None:
            return bad_request("nsfw cannot be null")
        game.set_nsfw(data.nsfw)

    if "steam_id" in sent and data.steam_id != game.steam_id:
        if data.steam_id is not None:
            other = GameSelect.by_steam_id(data.steam_id)
            if other and other.get_id() != game.get_id():
                return bad_request(
                    f"Steam ID already belongs to '{other.get_label()}' (id: {other.get_id()})"
                )
        game.set_steam_id(data.steam_id)

    if "parent_id" in sent and data.parent_id != game.parent_id:  # type: ignore
        parent = None
        if data.parent_id is not None:
            parent = __get_game(data.parent_id)
        try:
            game.set_parent(parent)
        except ValueError as e:
            return bad_request(str(e))

    hidden_changed = False
    if "hidden" in sent:
        if data.hidden is None:
            return bad_request("hidden cannot be null")
        hidden_changed = data.hidden != bool(game.hidden)
        if hidden_changed:
            game.set_hidden(data.hidden)

    game.save()
    if hidden_changed:
        sync_activities_hidden(game)
    return Admin_GameDetails.from_game(game)


@router.put("/game/{game_id}/igdb", response_model=Admin_GameDetails)
def set_igdb_id(game_id: int, data: Admin_SetIGDB) -> Admin_GameDetails:
    game = __get_game(game_id)
    igdb_id = data.igdb_id

    if igdb_id == 0 or igdb_id is None:
        game.set_igdb_id(igdb_id)
        game.save()
        return Admin_GameDetails.from_game(game)

    other = GameSelect.by_igdb_id(igdb_id)
    if other and other.get_id() != game.get_id():
        # it's the same game, they should be merged instead
        return bad_request(
            f"IGDB ID already belongs to '{other.get_label()}' (id: {other.get_id()}), merge the games instead"
        )

    igdb_game = igdb.get_game_info(igdb_id)
    if not igdb_game or not igdb_game.name:
        return not_found("Game not found in IGDB (or IGDB is not enabled)")

    # if another game has the IGDB name, keep our name
    adopt_name(game, igdb_game.name, "IGDB")
    if igdb_game.first_release_date:
        year = ts_to_dt(igdb_game.first_release_date).year
        if year != game.get_release_year():
            game.set_release_year(year)
    game.set_igdb_id(igdb_id, igdb_game.url)
    game.save()
    return Admin_GameDetails.from_game(game)


@router.post("/game/{game_id}/aliases", response_model=Admin_GameDetails)
def add_alias(game_id: int, data: Admin_Alias) -> Admin_GameDetails:
    game = __get_game(game_id)
    alias = data.alias.strip()
    if not alias:
        return bad_request("Alias cannot be empty")
    other = GameSelect.by_name_or_alias(alias)
    if other:
        return bad_request(
            f"Alias is already in use by '{other.get_label()}' (id: {other.get_id()})"
        )
    game.add_alias(alias)
    game.save()
    return Admin_GameDetails.from_game(game)


@router.delete("/game/{game_id}/aliases", response_model=Admin_GameDetails)
def remove_alias(game_id: int, alias: str = Query()) -> Admin_GameDetails:
    game = __get_game(game_id)
    if not game.remove_alias(alias):
        return not_found("Game doesn't have that alias")
    game.save()
    return Admin_GameDetails.from_game(game)


@router.delete("/game/{game_id}")
def delete_game(game_id: int, admin: AdminUser):
    game = __get_game(game_id)
    if activity_count(game=game) > 0:
        return bad_request("Game has activities, move or merge them first")
    if LiveActivity.select().where(LiveActivity.game == game).count() > 0:  # type: ignore
        return bad_request("Game has a live activity running")
    label = game.get_label()
    game.delete_instance()
    logger.info("Game %s '%s' deleted by admin %s", game_id, label, admin.get_name())
    return "Deleted"


@router.get("/game/{game_id}/merge", response_model=Admin_MergePreview)
def merge_preview(game_id: int, into: int = Query()) -> Admin_MergePreview:
    source = __get_game(game_id)
    target = __get_game(into)
    return Admin_MergePreview(
        activity_count=activity_count(game=source),
        new_aliases=merge_aliases(source, target),
    )


@router.post("/game/{game_id}/merge", response_model=Admin_Moved)
def merge_game(game_id: int, data: Admin_MergeGame) -> Admin_Moved:
    source = __get_game(game_id)
    target = __get_game(data.into_game_id)
    try:
        moved = merge_games(source, target)
    except ValueError as e:
        return bad_request(str(e))
    return Admin_Moved(moved=moved)


def __set_uploaded_cover(game_id: int, image: ImageFile | None) -> Admin_GameDetails:
    game = __get_game(game_id)
    game.set_uploaded_cover(image)
    game.save()
    return Admin_GameDetails.from_game(game)


def __upload_cover(game_id: int, data: bytes) -> Admin_GameDetails:
    __get_game(game_id)
    try:
        image = store_upload(data)
    except Exception as e:
        logger.warning("Upload for game %d is not an image we take: %s", game_id, e)
        return bad_request("Not an image (JPEG, PNG, WebP or GIF, at most 10 MB)")
    return __set_uploaded_cover(game_id, image)


@router.put("/game/{game_id}/cover", response_model=Admin_GameDetails)
async def upload_cover(game_id: int, request: Request) -> Admin_GameDetails:
    """the image is the request body, as is"""
    data = await request.body()
    # storing and making the versions is slow, keep it off the event loop
    return await run_in_threadpool(__upload_cover, game_id, data)


@router.put("/game/{game_id}/cover/url", response_model=Admin_GameDetails)
def cover_from_url(game_id: int, data: Admin_CoverUrl) -> Admin_GameDetails:
    __get_game(game_id)
    image = get_image(data.url.strip())
    if not image:
        return bad_request("Could not download an image from that URL")
    get_versions(image)
    return __set_uploaded_cover(game_id, image)


@router.delete("/game/{game_id}/cover", response_model=Admin_GameDetails)
def remove_cover(game_id: int) -> Admin_GameDetails:
    return __set_uploaded_cover(game_id, None)


@router.get("/igdb/search", response_model=list[IGDB_SearchResult])
def search_igdb(q: str = Query()) -> list[IGDB_SearchResult]:
    if not igdb.enabled():
        return service_unavailable("IGDB is not enabled")
    return igdb.search_game(q)


@router.get("/igdb/game/{igdb_id}", response_model=IGDB_GameInfo)
def igdb_game_info(igdb_id: int) -> IGDB_GameInfo:
    """for refreshing a game's name and release year from IGDB"""
    if not igdb.enabled():
        return service_unavailable("IGDB is not enabled")
    info = igdb.get_game_info(igdb_id)
    if not info:
        return not_found("Game not found on IGDB")
    return info
