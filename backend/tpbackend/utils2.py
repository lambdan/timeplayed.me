import datetime
import logging
import re
from typing import cast


logger = logging.getLogger("utils2")


def js_iso(d: datetime.datetime) -> str:
    """
    Shortcut for converting to YYYY-MM-DDTHH:MM:SSZ
    """
    d = assertTimezone(d)
    return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now() -> datetime.datetime:
    """
    Shortcut for current time in UTC
    """
    return datetime.datetime.now(datetime.UTC)


def now_iso(d: datetime.datetime | None = None) -> str:
    """
    Shortcut for current time in YYYY-MM-DDTHH:MM:SSZ
    """
    if d is None:
        d = now()
    return js_iso(d)


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
    if int(x) > int(maximum):
        return int(maximum)
    if int(x) < int(minimum):
        return int(minimum)
    return int(x)


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
        if ts < 10**12:  # if it's in seconds, convert to ms
            ts *= 1000
        return ts
    elif isinstance(ts, datetime.datetime):
        return dt_to_ts(ts)
    try:
        return validateTS(int(ts))
    except Exception as _:
        pass
    return None


def parseTS(ts) -> datetime.datetime | None:
    valid = validateTS(ts)
    if not valid:
        return None
    dt = datetime.datetime.fromtimestamp(valid / 1000)
    return assertTimezone(dt)


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


def assertTimezone(dt) -> datetime.datetime:
    assert isinstance(dt, datetime.datetime)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def dt_to_ts(dt: datetime.datetime) -> int:
    dt = assertTimezone(dt)
    return int(dt.timestamp() * 1000)


def ts_to_dt(ts: int) -> datetime.datetime:
    if ts < 10**12:  # if it's in seconds, convert to ms
        ts *= 1000
    return datetime.datetime.fromtimestamp(ts / 1000)


def parse_csv(input: int | str) -> list[int]:
    def ret(v):
        logger.info("parse_csv: '%s' -> %s", input, v)
        return v

    if isinstance(input, int):
        return ret([input])
    res = []
    input = input.replace("%2C", ",")  # replace url encoded
    for part in input.split(","):
        try:
            res.append(int(part))
        except Exception:
            continue
    return ret(res)
