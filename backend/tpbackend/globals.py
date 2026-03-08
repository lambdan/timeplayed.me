import logging
import os

DEBUG = os.environ.get("DEBUG") == "1"
LOGLEVEL_ENV = os.environ.get("LOGLEVEL", "").upper()

if DEBUG:
    print("⚠️⚠️⚠️ Running in DEBUG mode ⚠️⚠️⚠️")

ADMINS = os.environ.get("ADMINS", "").split(",") if os.environ.get("ADMINS") else []

TIMEPLAYED_URL = os.environ.get("TIMEPLAYED_URL", "").rstrip("/")


def game_url(game_id: int) -> str:
    """Return a markdown link to the game page, or an empty string if TIMEPLAYED_URL is not set."""
    if not TIMEPLAYED_URL:
        return ""
    return f"{TIMEPLAYED_URL}/game/{game_id}"


# CRITICAL, INFO , DEBUG, WARNING, ERROR

if LOGLEVEL_ENV == "CRITICAL":
    LOGLEVEL = logging.CRITICAL
elif LOGLEVEL_ENV == "ERROR":
    LOGLEVEL = logging.ERROR
elif LOGLEVEL_ENV == "WARNING":
    LOGLEVEL = logging.WARNING
elif LOGLEVEL_ENV == "DEBUG":
    LOGLEVEL = logging.DEBUG
else:
    LOGLEVEL = logging.INFO

logging.basicConfig(
    level=LOGLEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
