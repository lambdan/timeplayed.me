from fastapi import APIRouter

from tpbackend.storage import Game, Platform, User

router = APIRouter()


@router.post("/refresh_search")
def refresh_search():
    # saving rebuilds the search column
    for model in (Game, User, Platform):
        for row in model.select():
            row.save()
    return "Done"
