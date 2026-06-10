from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from tpbackend import bot
from tpbackend.cache import cache_set, cache_get


router = APIRouter()


@router.get(
    "/{discord_user_id}/avatar",
    tags=["Discord"],
    description="Redirects to URL for Discord avatar",
)
def redirect_discord_avatar(discord_user_id: str | int):
    def _get_url(discord_user_id: str | int) -> str:
        discord_user_id = int(discord_user_id)
        cache_key = f"get_discord_avatar_url:{discord_user_id}"
        cached = cache_get(cache_key)
        if cached:
            return cached.decode("utf-8")  # type: ignore
        url = bot.avatar_from_discord_user_id(discord_user_id)
        cache_set(cache_key, url, ex=3600)
        return url

    return RedirectResponse(_get_url(discord_user_id))
