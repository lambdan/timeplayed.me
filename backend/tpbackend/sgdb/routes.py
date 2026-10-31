from fastapi import APIRouter
from .models import SGDB_Grid
from .controller import available, get_grids, get_best_grid
from tpbackend.api.responses import not_found, service_unavailable

router = APIRouter()


@router.get(
    "/{sgdb_game_id}/grids/best",
    tags=["SteamGridDB"],
    response_model=SGDB_Grid,
    description="Tries to get the best grid for a game from SteamGridDB",
)
def best_grid_sgdb(sgdb_game_id: int) -> SGDB_Grid:
    if not available():
        return service_unavailable("SteamGridDB is not enabled")
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
    if not available():
        return service_unavailable("SteamGridDB is not enabled")
    return get_grids(sgdb_game_id)
