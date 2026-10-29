import logging
import os

DEBUG = os.environ.get("DEBUG") == "1"
LOGLEVEL_ENV = os.environ.get("LOGLEVEL", "").upper()

if DEBUG:
    print("⚠️⚠️⚠️ Running in DEBUG mode ⚠️⚠️⚠️")


TIMEPLAYED_URL = os.environ.get("TIMEPLAYED_URL", "http://localhost").rstrip("/")

MINIMUM_SESSION_LENGTH = int(os.environ.get("MINIMUM_SESSION_LENGTH", "0"))

# integrations, enabled by providing their credentials
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
SGDB_TOKEN = os.environ.get("SGDB_TOKEN", "")
IGDB_CLIENT_ID = os.environ.get("IGDB_CLIENT_ID", "")
IGDB_CLIENT_SECRET = os.environ.get("IGDB_CLIENT_SECRET", "")
DISCORD_ENABLED = bool(DISCORD_TOKEN)
SGDB_ENABLED = bool(SGDB_TOKEN)
IGDB_ENABLED = bool(IGDB_CLIENT_ID and IGDB_CLIENT_SECRET)
OBLIVIONIS_DB = os.environ.get("OBLIVIONIS_DB", "")
OBLIVIONIS_ENABLED = bool(OBLIVIONIS_DB)

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
