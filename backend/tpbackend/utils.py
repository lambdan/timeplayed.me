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
    User_or_none,
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


def game_url(game_id) -> str:
    """
    Returns the URL for a game page, or an empty string if TIMEPLAYED_URL is not set.
    """
    if not TIMEPLAYED_URL:
        return ""
    return f"{TIMEPLAYED_URL}/game/{game_id}"


def activity_url(activity_id) -> str:
    return f"{TIMEPLAYED_URL}/activity/{activity_id}"


def platform_url(platform_id) -> str:
    return f"{TIMEPLAYED_URL}/platform/{platform_id}"


def user_url(user_id) -> str:
    return f"{TIMEPLAYED_URL}/user/{user_id}"


def user_name(user: User, as_markdown_link=False) -> str:
    id = user.get_id()
    name = user.get_name().strip()
    if as_markdown_link:
        url = user_url(id)
        if url:
            return f"[{name}]({url})"
    return name


def activity_name(activity: Activity, as_markdown_link=False) -> str:
    id = activity.get_id()
    name = f"Activity {id}".strip()
    if as_markdown_link:
        url = activity_url(id)
        if url:
            return f"[{name}]({url})"
    return name


def game_name(game: Game, as_markdown_link=False) -> str:
    id = game.get_id()
    name = game.get_name().strip()
    year = game.get_release_year()
    if year:
        name += f" ({year})"
    name = name.strip()
    if as_markdown_link:
        url = game_url(id)
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


def search_users(query: str, offset=0, limit=0) -> list[User]:
    """
    Search users by name
    """
    query = query_normalize(query)
    users = []
    for user in User.select():
        user = cast(User, user)
        # search in name
        if query in query_normalize(user.get_name()):
            users.append(user)
            continue
        if query in query_normalize(str(user.get_discord_id())):
            users.append(user)
            continue
        if query in query_normalize(str(user.get_id())):
            users.append(user)
            continue
    logger.info("search_users :: '%s' --> %s results", query, len(users))
    # order by name
    users.sort(key=lambda u: cast(User, u).get_name().lower())
    # offset and limit
    if limit > 0:
        users = users[offset : offset + limit]
    else:
        users = users[offset:]
    return users
