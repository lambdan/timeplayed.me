from fastapi import APIRouter

from tpbackend.cache import get_cache_stats
from tpbackend.storage import Game, Platform, User

router = APIRouter()


@router.get("/cache_stats", response_model=str)
def cache_stats() -> str:
    return get_cache_stats()


@router.post("/refresh_search")
def refresh_search():
    # saving rebuilds the search column
    for model in (Game, User, Platform):
        for row in model.select():
            row.save()
    return "Done"
