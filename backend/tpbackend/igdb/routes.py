from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from tpbackend.api.responses import not_found
from tpbackend.igdb.controller import get_cover_for_game


router = APIRouter()


@router.get(
    "/{igdb_game_id}/cover",
    tags=["IGDB"],
    description="Redirects to cover image for a game from IGDB",
)
def redirect_igdb_cover(igdb_game_id: int):
    cover = get_cover_for_game(igdb_game_id)
    if cover:
        return RedirectResponse(cover)
    return not_found("Did not find cover for that game")
