from fastapi import APIRouter
from tpbackend.api_v2.sgdb.models import SGDB_Game, SGDB_Grid
from tpbackend.api_v2.sgdb.controller import search, get_grids, get_best_grid


router = APIRouter()


@router.get(
    "/search",
    tags=["SteamGridDB"],
    response_model=list[SGDB_Game] | None,
    description="Searches SteamGridDB for games",
)
def search_sgdb(query: str) -> list[SGDB_Game] | None:
    return search(query)


@router.get(
    "/{sgdb_game_id}/grids/best",
    tags=["SteamGridDB"],
    response_model=SGDB_Grid | None,
    description="Tries to get the best grid for a game from SteamGridDB",
)
def best_grid_sgdb(sgdb_game_id: int) -> SGDB_Grid | None:
    return get_best_grid(sgdb_game_id)


@router.get(
    "/{sgdb_game_id}/grids",
    tags=["SteamGridDB"],
    response_model=list[SGDB_Grid] | None,
    description="Gets grids for a game from SteamGridDB",
)
def sgdb_grids(sgdb_game_id: int) -> list[SGDB_Grid] | None:
    return get_grids(sgdb_game_id)
