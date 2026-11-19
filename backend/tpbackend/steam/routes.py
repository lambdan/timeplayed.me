from fastapi import APIRouter

from tpbackend.api.responses import not_found
from .controller import get_cover_url, store_url
from .models import Steam_Cover

router = APIRouter()


@router.get(
    "/{app_id}/cover",
    tags=["Steam"],
    response_model=Steam_Cover,
    description="Gets the 600x900 library cover of a Steam app",
)
def steam_cover(app_id: int) -> Steam_Cover:
    url = get_cover_url(app_id)
    if not url:
        return not_found("Steam has no cover for this app")
    return Steam_Cover(url=url, store_url=store_url(app_id))
