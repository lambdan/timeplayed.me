import datetime
from xml.sax.saxutils import escape

from fastapi import APIRouter, Response
from peewee import fn

from tpbackend.game.utils import game_url
from tpbackend.globals import TIMEPLAYED_URL
from tpbackend.platform.utils import platform_url
from tpbackend.storage import Activity, Game
from tpbackend.user.utils import user_url

sitemap_router = APIRouter()

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


def __url_entry(url: str, lastmod: datetime.datetime | None = None) -> str:
    entry = f"<url><loc>{escape(url)}</loc>"
    if lastmod:
        entry += f"<lastmod>{lastmod.date().isoformat()}</lastmod>"
    return entry + "</url>"


@sitemap_router.get("/sitemap.xml", tags=["misc"], response_class=Response)
def sitemap() -> Response:
    """
    Sitemap for search engines, with every game, user and platform that has playtime
    """
    entries = [__url_entry(f"{TIMEPLAYED_URL}{path}") for path in STATIC_PATHS]

    games = __last_activity_per(Activity.game)
    visible_game_ids = [
        g.get_id()
        for g in Game.select().where(Game.id.in_(list(games.keys())))  # type: ignore
        if not g.get_hidden()
    ]
    for game_id in sorted(visible_game_ids):
        entries.append(__url_entry(game_url(game_id), games[game_id]))

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
    return Response(content=xml, media_type="application/xml")
