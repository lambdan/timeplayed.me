import redis
import os
import logging

logger = logging.getLogger("cache")

__REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
__REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
__REDIS_CLIENT = redis.Redis(host=__REDIS_HOST, port=__REDIS_PORT, db=0)

__CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
__CACHE_DEFAULT_EX = int(os.environ.get("CACHE_DEFAULT_EX", 10))
__CACHE_LOG_ENABLED = os.environ.get("CACHE_LOG_ENABLED", "false").lower() == "true"


def __log(message: str):
    if not __CACHE_LOG_ENABLED:
        return
    logger.info(message)


def __warn(message: str):
    if not __CACHE_LOG_ENABLED:
        return
    logger.warning(message)


def __error(message: str):
    if not __CACHE_LOG_ENABLED:
        return
    logger.error(message)


def cache_get(key: str):
    if __CACHE_ENABLED:
        try:
            cached = __REDIS_CLIENT.get(key)
            if cached:
                __log(f"Hit: {key}")
                return cached
            __warn(f"Miss: {key}")
        except Exception as e:
            __error(f"Exception caught getting cache for key {key}: {e}")
    return None


def cache_set(key: str, value: str, ex=__CACHE_DEFAULT_EX):
    if __CACHE_ENABLED:
        try:
            __REDIS_CLIENT.set(key, value, ex=ex)
            __log(f"Set: {key} (expires in {ex} seconds)")
        except Exception as e:
            __error(f"Exception caught setting cache for key {key}: {e}")
