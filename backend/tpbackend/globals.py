import logging
import os

DEBUG = os.environ.get("DEBUG") == "1"
LOGLEVEL_ENV = os.environ.get("LOGLEVEL", "").upper()

if DEBUG:
    print("⚠️⚠️⚠️ Running in DEBUG mode ⚠️⚠️⚠️")

ADMINS = os.environ.get("ADMINS", "").split(",") if os.environ.get("ADMINS") else []


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
