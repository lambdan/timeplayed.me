"""
<head> tags for pages, included by nginx (SSI) when serving index.html, so search
engines and link previews (Discord etc) see the right title and description without
running JavaScript.

An empty response means "use the defaults in index.html".
"""

from html import escape

from fastapi import APIRouter, Response

from tpbackend.game.models import API_GameWithStats
from tpbackend.game.query import GameStatsQuery
from tpbackend.game.utils import game_url
from tpbackend.platform.models import API_PlatformWithStats
from tpbackend.platform.query import PlatformStatsQuery
from tpbackend.platform.utils import platform_url
from tpbackend.storage import Game
from tpbackend.user.models import API_UserWithStats
from tpbackend.user.query import UserStatsQuery
from tpbackend.user.utils import user_url

head_router = APIRouter()


def format_playtime(seconds: int) -> str:
    """
    Same style as formatDuration() in the frontend, e.g. "504.7 hours" or "12 minutes"
    """
    hours = seconds / 3600
    if hours > 1.5:
        return f"{hours:.1f} hours"
    minutes = seconds // 60
    if minutes == 1:
        return "1 minute"
    if minutes > 1:
        return f"{minutes} minutes"
    return f"{seconds} seconds"


def plural(count: int, word: str) -> str:
    if count == 1:
        return f"{count} {word}"
    return f"{count} {word}s"


def head_tags(title: str, description: str, url: str) -> str:
    title = escape(f"{title} - Timeplayed.me")
    description = escape(description)
    url = escape(url)
    return "\n".join(
        [
            f"<title>{title}</title>",
            f'<meta name="description" content="{description}" />',
            f'<link rel="canonical" href="{url}" />',
            '<meta property="og:site_name" content="Timeplayed.me" />',
            '<meta property="og:type" content="website" />',
            f'<meta property="og:title" content="{title}" />',
            f'<meta property="og:description" content="{description}" />',
            f'<meta property="og:url" content="{url}" />',
        ]
    )


def game_head(game_id: int) -> str:
    game = Game.get_or_none(Game.id == game_id)
    if game is None or game.get_hidden():
        return ""
    query = GameStatsQuery.apply_ids(GameStatsQuery.base(), [game_id])
    stats = API_GameWithStats.from_game(query.get()).stats

    name = game.name
    if game.release_year:
        name += f" ({game.release_year})"
    description = (
        f"{name}: {format_playtime(stats.seconds)} played by "
        f"{plural(stats.user_count, 'player')}. "
        "Top players, recent sessions and playtime history."
    )
    return head_tags(f"{name} playtime", description, game_url(game_id))


def user_head(user_id: int) -> str:
    query = UserStatsQuery.apply_ids(UserStatsQuery.base(), [user_id])
    user = query.get_or_none()
    if user is None:
        return ""
    api_user = API_UserWithStats.from_user(user)

    name = api_user.display_name
    stats = api_user.stats
    description = (
        f"{name}: {format_playtime(stats.seconds)} played across "
        f"{plural(stats.game_count, 'game')}. "
        "Top games, platforms and recent activity."
    )
    return head_tags(f"{name} playtime", description, user_url(user_id))


def platform_head(platform_id: int) -> str:
    query = PlatformStatsQuery.apply_ids(PlatformStatsQuery.base(), [platform_id])
    platform = query.get_or_none()
    if platform is None:
        return ""
    api_platform = API_PlatformWithStats.from_platform(platform)

    name = api_platform.display_name
    stats = api_platform.stats
    description = (
        f"{name}: {format_playtime(stats.seconds)} played across "
        f"{plural(stats.game_count, 'game')} by "
        f"{plural(stats.user_count, 'player')}. "
        "Top games, top players and recent activity."
    )
    return head_tags(f"{name} playtime", description, platform_url(platform_id))


PAGES = {
    "game": game_head,
    "user": user_head,
    "platform": platform_head,
}


@head_router.get("/head/{path:path}", include_in_schema=False)
def head(path: str) -> Response:
    """
    path is the page path, e.g. "game/123"
    """
    html = ""
    parts = path.strip("/").split("/")
    if len(parts) == 2 and parts[0] in PAGES and parts[1].isdigit():
        html = PAGES[parts[0]](int(parts[1]))
    return Response(content=html, media_type="text/html")
