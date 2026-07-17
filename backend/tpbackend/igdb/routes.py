from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from tpbackend.api.responses import not_found, service_unavailable
from tpbackend.igdb.controller import available, get_game_info
from tpbackend.igdb.models import IGDB_GameInfo


router = APIRouter()


@router.get(
    "/game/{igdb_game_id}",
    tags=["IGDB"],
    description="Get game info from IGDB by their ID",
    response_model=IGDB_GameInfo | None,
)
def get_igdb_game_info(igdb_game_id: int) -> IGDB_GameInfo | None:
    if not available():
        return service_unavailable()
    game_info = get_game_info(igdb_game_id)
    if game_info:
        return game_info
    return not_found()
