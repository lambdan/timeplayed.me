import datetime
import logging
import re

from tpbackend.storage import storage_v2

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
    Returns 0 on failure
    """
    if isinstance(ts, int) and ts > 0:
        return ts
    try:
        return validateTS(int(ts))
    except Exception as _:
        pass
    return None


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


def tsFromActivity(activity: storage_v2.Activity) -> int:
    """
    Returns a timestamp in milliseconds from an Activity
    """
    dt = activity.timestamp
    if isinstance(dt, int):
        # logger.info("tsFromActivity :: Returning %s", dt)
        return dt
    if dt.tzinfo is None:  # type: ignore
        dt = dt.replace(tzinfo=datetime.timezone.utc)  # type: ignore
    res = int(dt.timestamp() * 1000)  # type: ignore
    # logger.info("tsFromActivity :: Returning %s", res)
    return res


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
    res = ""
    for c in q:
        # only keep A-Z, 0-9 and space
        if c.isalnum() or c == " ":
            res += c
    # logger.info("query_normalize :: '%s' --> '%s'", q, res)
    return res


def search_games(query: str, offset=0, limit=0) -> list[storage_v2.Game]:
    """
    Search games by name or alias
    """
    # TODO: cache/optimize :) this probably pretty slow once we have thousands of games
    query = query_normalize(query)
    games = []
    for game in storage_v2.Game.select():
        # search in name
        # game.name is cleaned as well, eg to allow
        # "belmonts revenge" to match "Belmont's Revenge"
        if query in query_normalize(game.name):
            games.append(game)
            continue
        if not game.aliases or len(game.aliases) == 0:
            # no aliases
            continue
        for alias in game.aliases:
            if query in query_normalize(alias):
                games.append(game)
                break
    logger.info("search_games :: '%s' --> %s results", query, len(games))
    if len(games) == 0 and " " in query and offset == 0:
        # nothing found, we can try removing a term and go again
        parts = query.split(" ")
        last_term_removed = " ".join(parts[:-1])
        return search_games(query=last_term_removed, offset=offset, limit=limit)
    # order by name
    games.sort(key=lambda g: g.name.lower())
    # offset and limit
    if limit > 0:
        games = games[offset : offset + limit]
    else:
        games = games[offset:]
    return games


def search_platforms(query: str, offset=0, limit=0) -> list[storage_v2.Platform]:
    """
    Search platforms by name or alias
    """
    query = query_normalize(query)
    platforms = []
    for platform in storage_v2.Platform.select():
        platform: storage_v2.Platform
        # search in abbreviation
        if platform.abbreviation and query in query_normalize(
            str(platform.abbreviation)
        ):
            platforms.append(platform)
            continue
        # search in name
        if platform.name and query in query_normalize(str(platform.name)):
            platforms.append(platform)
            continue
    logger.info("search_platforms :: '%s' --> %s results", query, len(platforms))
    # order by abbreviation
    platforms.sort(key=lambda p: p.abbreviation.lower())
    # offset and limit
    if limit > 0:
        platforms = platforms[offset : offset + limit]
    else:
        platforms = platforms[offset:]
    return platforms
