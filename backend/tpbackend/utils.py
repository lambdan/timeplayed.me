import datetime
import logging
import re
from typing import cast

from tpbackend.globals import TIMEPLAYED_URL
from tpbackend.storage import storage_v2
from tpbackend.storage.storage_v2 import Game, Activity, Platform, User

logger = logging.getLogger("utils")


def now() -> datetime.datetime:
    """
    Shortcut for current time in UTC
    """
    return datetime.datetime.now(datetime.UTC)


def datetimeParse(s: str) -> datetime.datetime | None:
    """
    Parses an datetime from a JS-like ISO8601 string (`YYYY-MM-DDTHH:MM:SSZ`)
    or
    relative time (-1h30m5s)
    """
    if s.startswith("-"):
        s = s.lower().strip()
        s = s[1:]  # Remove the leading '-' for easier parsing
        if ":" in s:
            parts = s.split(":")
            if len(parts) != 3:
                return None
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return now() - datetime.timedelta(
                hours=hours, minutes=minutes, seconds=seconds
            )
        hours = 0
        mins = 0
        secs = 0
        if "h" in s:
            hours = s.split("h")[0]
            s = s.replace(hours + "h", "")
            hours = int(hours)
        if "m" in s:
            mins = s.split("m")[0]
            s = s.replace(mins + "m", "")
            mins = int(mins)
        if "s" in s:
            secs = s.split("s")[0]
            s = s.replace(secs + "s", "")
            secs = int(secs)
        return now() - datetime.timedelta(hours=hours, minutes=mins, seconds=secs)

    try:
        s = s.upper().strip()
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception as _:
        return None


def secsToHHMMSS(secs: int) -> str:
    """
    Returns a string in HH:MM:SS format
    """
    if secs < 0:
        return "00:00:00"
    try:
        hours = secs // 3600
        minutes = (secs % 3600) // 60
        seconds = secs % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    except Exception as e:
        logger.error("Error converting seconds to HH:MM:SS format: %s", e)
        return "00:00:00"


def secsFromString(s: str) -> int | None:
    """
    Turns a duration string into seconds.
    Supported formats:
    - HH:MM:SS (e.g., 01:30:45)
    - HhMmSs (e.g., 1h30m45s)
    - Just a number (e.g., 3600 = 1 hour)
    Returns None on error
    """
    try:
        s = s.strip().lower().replace(" ", "")
        if ":" in s:
            parts = s.split(":")
            if len(parts) != 3:
                return None
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif "h" in s or "m" in s or "s" in s:
            hours = minutes = seconds = 0
            if "h" in s:
                hours = int(s.split("h")[0])
            if "m" in s:
                minutes = int(s.split("m")[0].split("h")[-1])
            if "s" in s:
                seconds = int(s.split("s")[0].split("m")[-1])
            return hours * 3600 + minutes * 60 + seconds
        else:
            return int(s)
    except Exception as e:
        logger.error("Error parsing duration string '%s': %s", s, e)
        return None


def parseRange(s: str) -> tuple[int, int] | None:
    """
    Attempts to parse a range in the format a-b
    """
    try:
        parts = s.split("-")
        if len(parts) != 2:
            return None
        start = int(parts[0])
        end = int(parts[1])
        return (start, end)
    except Exception as _:
        return None


def normalizeQuotes(s: str) -> str:
    """
    Remove dumb Apple quotes and replaces them with standard quotes
    """
    return (
        s.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("’", "'")
        .replace("`", "'")
        .replace("´", "'")
    )


def validateDate(date: datetime.datetime) -> str:
    """
    Returns OK if valid
    """
    now = datetime.datetime.now(datetime.UTC)
    if date > now:
        return "Date cannot be in the future"

    if date < datetime.datetime(2025, 1, 20, tzinfo=datetime.UTC):
        return "Date cannot be before 2025-01-20 (timeplayed started then!)"

    return "OK"


def clamp(x: int, minimum: int, maximum: int) -> int:
    """
    Clamps x between minimum and maximum
    """
    return max(int(minimum), min(int(x), int(maximum)))


def max_int(x: int, minimum: int) -> int:
    """
    Like regular max but ensures both are ints
    """
    return max(int(minimum), int(x))


def today() -> str:
    """
    Returns the current date in the format YYYY-MM-DD
    """
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d")


def thisHour() -> str:
    """
    Returns the current hour in the format YYYY-MM-DD_HH
    """
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d_%H")


def validateTS(ts) -> int | None:
    """
    Validates a timestamp (int > 0).
    Also tries to convert to int if possible.
    Returns None on failure
    """
    if isinstance(ts, int) and ts > 0:
        return ts
    try:
        return validateTS(int(ts))
    except Exception as _:
        pass
    return None


def truncateMilliseconds(ts: int) -> int:
    return (ts // 1000) * 1000


def sanitize(s: str) -> str:
    logger.info("Sanitize in: %s", s)

    if s.startswith('"'):
        s = s[1:]
    if s.endswith('"'):
        s = s[:-1]
    if s.startswith("'"):
        s = s[1:]
    if s.endswith("'"):
        s = s[:-1]

    s = s.replace("\n", "")

    # remove double quotes and escaped double quotes
    s = s.replace('"', "").replace('\\"', "")

    # functions... kind of
    s = s.replace("('", "").replace("')", "")
    s = s.replace(";(", "").replace(");", "")

    # remove backslashes
    s = s.replace("\\", "")

    # remove html tags
    s = re.sub(r"<[^>]*?>", "", s)

    # remove urls
    s = s.replace("http://", "")
    s = s.replace("https://", "")

    logger.info("Sanitize out: %s", s)
    return s


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
        platform = storage_v2.Platform.get_or_none(storage_v2.Platform.id == last_activity.platform_id)  # type: ignore
        return platform
    except Exception as e:
        logger.error("last_platform_for_game :: exception: %s", e)
        pass
    return None


def query_normalize(q: str) -> str:
    q = q.lower().strip()
    q = q.replace(" ", " ")  # replace nbsp with regular space
    while "  " in q:
        q = q.replace("  ", " ")  # replace multiple spaces with single space
    res = ""
    for c in q:
        # Pokémon --> pokemon...
        if c in "àáâäåä":
            c = "a"
        if c in "ç":
            c = "c"
        if c in "éèêë":
            c = "e"
        if c in "îïíì":
            c = "i"
        if c in "ñ":
            c = "n"
        if c in "öòóôõøö":
            c = "o"
        if c in "ùúûü":
            c = "u"
        if c in "ÿ":
            c = "y"
        # only keep A-Z, 0-9 and space
        if c.isalnum() or c == " ":
            res += c
    # logger.info("query_normalize :: '%s' --> '%s'", q, res)
    return res


def search_games(
    query: str, offset=0, limit=0, include_hidden=False
) -> list[storage_v2.Game]:
    """
    Search games by name or alias
    """
    # TODO: cache/optimize :) this probably pretty slow once we have thousands of games
    query = query_normalize(query)
    games = []
    for game in storage_v2.Game.select():
        game = cast(Game, game)
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


def assertTimezone(dt) -> datetime.datetime:
    assert isinstance(dt, datetime.datetime)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt
