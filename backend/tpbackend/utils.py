import datetime
import logging
from typing import cast

from tpbackend.utils2 import query_normalize
from tpbackend.globals import TIMEPLAYED_URL
from tpbackend.storage import storage_v2
from tpbackend.storage.storage_v2 import (
    Game,
    Activity,
    Platform,
    Platform_or_none,
    User,
    User_or_none,
)

logger = logging.getLogger("utils")


def last_platform_for_game(
    user: storage_v2.User, game: storage_v2.Game
) -> storage_v2.Platform | None:
    """
    Returns the last platform the user played the game on if available
    """
    try:
        last_activity = (
            storage_v2.Activity.select()
            .where(
                (storage_v2.Activity.user == user) & (storage_v2.Activity.game == game)
            )
            .order_by(storage_v2.Activity.timestamp.desc())
            .first()
        )
        if not last_activity:
            return None
        return Platform_or_none(last_activity.platform_id)
    except Exception as e:
        logger.error("last_platform_for_game :: exception: %s", e)
        pass
    return None


def search_games_for_api(
    query: str, offset: int, limit: int, userId: int | None = None
) -> tuple[list[storage_v2.Game], int]:
    """
    Search games by name or alias, and return total count for pagination
    """
    # this is craaaaaazzzyyy ineffective
    all_games = search_games(
        query=query, offset=0, limit=0, include_hidden=False, userId=userId
    )
    total_count = len(all_games)
    games = all_games[offset : offset + limit]
    return games, total_count


CACHED_SEARCHES = {}
CACHED_SEARCHES_WIPED = 0


def search_games(
    query: str, offset=0, limit=0, include_hidden=False, userId: int | None = None
) -> list[storage_v2.Game]:
    query = query_normalize(query)
    key = f"search_games:{query}:{include_hidden}:{offset}:{limit}:{userId}"

    # clean up cache first
    global CACHED_SEARCHES_WIPED
    cache_age = datetime.datetime.now().timestamp() - CACHED_SEARCHES_WIPED
    if cache_age > 30 or len(CACHED_SEARCHES) > 30:
        CACHED_SEARCHES.clear()
        CACHED_SEARCHES_WIPED = datetime.datetime.now().timestamp()

    if key in CACHED_SEARCHES:
        logger.info("search_games :: cache hit for key '%s'", key)
        return CACHED_SEARCHES[key]

    games = []
    for game in storage_v2.Game.select():
        game = cast(Game, game)
        user = User_or_none(userId)
        if user and not game.user_has_played(user):
            continue
        if not include_hidden and game.get_hidden():
            continue
        # search in name
        # game.name is cleaned as well, eg to allow
        # "belmonts revenge" to match "Belmont's Revenge"
        if query in query_normalize(game.get_name()):
            games.append(game)
            continue
        if len(game.get_aliases()) == 0:
            continue
        for alias in game.get_aliases():
            if query in query_normalize(alias):
                games.append(game)
                break
    logger.info("search_games :: '%s' --> %s results", query, len(games))
    if len(games) == 0 and " " in query and offset == 0:
        # nothing found, we can try removing a term and go again
        parts = query.split(" ")
        last_term_removed = " ".join(parts[:-1])
        return search_games(
            query=last_term_removed,
            offset=offset,
            limit=limit,
            include_hidden=include_hidden,
        )
    # order by name
    games.sort(key=lambda g: g.get_name().lower())
    # offset and limit
    if limit > 0:
        games = games[offset : offset + limit]
    else:
        games = games[offset:]

    CACHED_SEARCHES[key] = games
    return games


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


def search_platforms(query: str, offset=0, limit=0) -> list[storage_v2.Platform]:
    """
    Search platforms by name or alias
    """
    query = query_normalize(query)
    platforms = []
    for platform in storage_v2.Platform.select():
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


def search_users(query: str, offset=0, limit=0) -> list[storage_v2.User]:
    """
    Search users by name
    """
    query = query_normalize(query)
    users = []
    for user in storage_v2.User.select():
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
