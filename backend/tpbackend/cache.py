import redis
import os
import logging

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_CLIENT = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

logger = logging.getLogger("cache")

CACHE_LOG_ENABLED = os.environ.get("CACHE_LOG_ENABLED", "true").lower() == "true"


def log(message: str):
    if not CACHE_LOG_ENABLED:
        return
    logger.info(message)


def warn(message: str):
    if not CACHE_LOG_ENABLED:
        return
    logger.warning(message)


def error(message: str):
    if not CACHE_LOG_ENABLED:
        return
    logger.error(message)


def cacheGet(key: str):
    try:
        cached = REDIS_CLIENT.get(key)
        if cached:
            log(f"Hit: {key}")
            return cached
        warn(f"Miss: {key}")
    except Exception as e:
        error(f"Exception caught getting cache for key {key}: {e}")
    return None


def cacheSet(key: str, value: str, ex=60):
    try:
        REDIS_CLIENT.set(key, value, ex=ex)
        log(f"Set: {key} (expires in {ex} seconds)")
    except Exception as e:
        error(f"Exception caught setting cache for key {key}: {e}")
