import datetime
import logging
from typing import cast

from tpbackend.utils2 import query_normalize
from tpbackend.globals import TIMEPLAYED_URL
from .storage import (
    Game,
    Activity,
    Platform,
    Platform_or_none,
    User,
)

logger = logging.getLogger("utils")


def last_platform_for_game(user: User, game: Game) -> Platform | None:
    """
    Returns the last platform the user played the game on if available
    """
    try:
        last_activity = (
            Activity.select()
            .where((Activity.user == user) & (Activity.game == game))
            .order_by(Activity.timestamp.desc())
            .first()
        )
        if not last_activity:
            return None
        return Platform_or_none(last_activity.platform_id)
    except Exception as e:
        logger.error("last_platform_for_game :: exception: %s", e)
        pass
    return None


def activity_url(activity_id) -> str:
    return f"{TIMEPLAYED_URL}/activity/{activity_id}"


def platform_url(platform_id) -> str:
    return f"{TIMEPLAYED_URL}/platform/{platform_id}"


def activity_name(activity: Activity, as_markdown_link=False) -> str:
    id = activity.get_id()
    name = f"Activity {id}".strip()
    if as_markdown_link:
        url = activity_url(id)
        if url:
            return f"[{name}]({url})"
    return name


def platform_name(platform: Platform, as_markdown_link=False) -> str:
    id = platform.get_id()
    name = platform.get_display_name()
    if as_markdown_link:
        url = platform_url(id)
        if url:
            return f"[{name}]({url})"
    return name


def search_platforms(query: str, offset=0, limit=0) -> list[Platform]:
    """
    Search platforms by name or alias
    """
    query = query_normalize(query)
    platforms = []
    for platform in Platform.select():
        platform = cast(Platform, platform)
        # search in abbreviation
        if query in query_normalize(platform.get_abbreviation()):
            platforms.append(platform)
            continue
        # search in name
        name = platform.get_name()
        if name and query in query_normalize(name):
            platforms.append(platform)
            continue
    logger.info("search_platforms :: '%s' --> %s results", query, len(platforms))
    # order by abbreviation
    platforms.sort(key=lambda p: cast(Platform, p).get_abbreviation().lower())
    # offset and limit
    if limit > 0:
        platforms = platforms[offset : offset + limit]
    else:
        platforms = platforms[offset:]
    return platforms
