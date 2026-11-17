import datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, Response
from peewee import fn

from tpbackend.api.responses import not_found
from tpbackend.cache import cache_get, cache_set
from tpbackend.game.utils import game_url
from tpbackend.globals import FALLBACK_URL, timeplayed_url
from tpbackend.platform.utils import platform_url
from tpbackend.storage import Activity, Game
from tpbackend.user.utils import user_url

sitemap_router = APIRouter()

SITEMAP_CACHE_KEY = "sitemap"

STATIC_PATHS = [
    "/",
    "/games",
    "/users",
    "/platforms",
    "/stats",
    "/browse",
    "/news",
    "/help",
]


def __last_activity_per(field) -> dict[int, datetime.datetime]:
    """
    Latest visible activity timestamp per id of field (Activity.game/user/platform)
    """
    query = (
        Activity.select(field, fn.MAX(Activity.timestamp).alias("last"))
        .where(Activity.hidden == False)  # noqa: E712
        .group_by(field)
        .tuples()
    )
    return {id: last for id, last in query}


def __hidden_game_ids() -> set[int]:
    """
    Ids of hidden games, including games with a hidden parent. Same as
    Game.get_hidden(), but with one query instead of one per parent
    """
    games = {
        id: (hidden, parent_id)
        for id, hidden, parent_id in Game.select(
            Game.id, Game.hidden, Game.parent
        ).tuples()
    }
    hidden_ids = set()
    for game_id in games:
        current = game_id
        seen = set()
        while current is not None and current not in seen:
            seen.add(current)
            hidden, parent_id = games[current]
            if hidden:
                hidden_ids.add(game_id)
                break
            current = parent_id
    return hidden_ids


def __url_entry(url: str, lastmod: datetime.datetime | None = None) -> str:
    entry = f"<url><loc>{escape(url)}</loc>"
    if lastmod:
        entry += f"<lastmod>{lastmod.date().isoformat()}</lastmod>"
    return entry + "</url>"


@sitemap_router.get("/sitemap.xml", response_class=Response, include_in_schema=False)
def sitemap() -> Response:
    """
    Sitemap for search engines, with every game, user and platform that has playtime
    """
    # Sitemap urls have to be absolute
    base_url = timeplayed_url()
    if base_url == FALLBACK_URL:
        not_found("Sitemap needs TIMEPLAYED_URL to be set")

    cached = cache_get(SITEMAP_CACHE_KEY)
    if cached:
        return Response(content=cached, media_type="application/xml")

    entries = [__url_entry(f"{base_url}{path}") for path in STATIC_PATHS]

    hidden_game_ids = __hidden_game_ids()
    for game_id, last in sorted(__last_activity_per(Activity.game).items()):
        if game_id not in hidden_game_ids:
            entries.append(__url_entry(game_url(game_id), last))

    for user_id, last in sorted(__last_activity_per(Activity.user).items()):
        entries.append(__url_entry(user_url(user_id), last))

    for platform_id, last in sorted(__last_activity_per(Activity.platform).items()):
        entries.append(__url_entry(platform_url(platform_id), last))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    cache_set(SITEMAP_CACHE_KEY, xml, ex=3600)
    return Response(content=xml, media_type="application/xml")
