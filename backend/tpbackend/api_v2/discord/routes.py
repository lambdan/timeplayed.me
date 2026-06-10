from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from tpbackend.api_v2.discord.controller import get_avatar_url

router = APIRouter()


@router.get(
    "/{discord_user_id}/avatar",
    tags=["Discord"],
    description="Redirects to URL for Discord avatar",
)
def redirect_discord_avatar(discord_user_id: str | int):
    url = get_avatar_url(discord_user_id)
    return RedirectResponse(url)
