from fastapi import APIRouter
from .models import SGDB_Grid
from .controller import get_grids, get_best_grid, get_grid
from tpbackend.api.responses import not_found


router = APIRouter()


@router.get(
    "/{sgdb_game_id}/grids/best",
    tags=["SteamGridDB"],
    response_model=SGDB_Grid,
    description="Tries to get the best grid for a game from SteamGridDB",
)
def best_grid_sgdb(sgdb_game_id: int) -> SGDB_Grid:
    best = get_best_grid(sgdb_game_id)
    if not best:
        return not_found("Could not find best grid")
    return best


@router.get(
    "/{sgdb_game_id}/grids",
    tags=["SteamGridDB"],
    response_model=list[SGDB_Grid],
    description="Gets grids for a game from SteamGridDB",
)
def sgdb_grids(sgdb_game_id: int) -> list[SGDB_Grid] | None:
    return get_grids(sgdb_game_id)


@router.get(
    "/{sgdb_game_id}/grids/{grid_id}",
    tags=["SteamGridDB"],
    response_model=SGDB_Grid,
    description="Gets a grid by ID for a game from SteamGridDB",
)
def sgdb_grid_by_id(sgdb_game_id: int, grid_id: int) -> SGDB_Grid:
    grid = get_grid(game_id=sgdb_game_id, grid_id=grid_id)
    if grid:
        return grid
    return not_found("Could not find grid with that ID for that game")
