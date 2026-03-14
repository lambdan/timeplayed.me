import redis
import os
import logging

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_CLIENT = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

logger = logging.getLogger("cache")

CACHE_ENABLED = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
CACHE_LOG_ENABLED = os.environ.get("CACHE_LOG_ENABLED", "false").lower() == "true"

__STATS = {}


def __log(message: str):
    if not CACHE_LOG_ENABLED:
        return
    logger.info(message)


def __warn(message: str):
    if not CACHE_LOG_ENABLED:
        return
    logger.warning(message)


def __error(message: str):
    if not CACHE_LOG_ENABLED:
        return
    logger.error(message)


def get_cache_stats() -> str:
    hits = sum(s["hit"] for s in __STATS.values())
    misses = sum(s["miss"] for s in __STATS.values())
    total = hits + misses
    hit_rate = (hits / total * 100) if total > 0 else 0
    stats = f"Cache stats: {total} total, {hits} hits, {misses} misses, hit rate: **{hit_rate:.2f}%**\n"
    # sort origins by count desc
    sorted_stats = sorted(
        __STATS.items(), key=lambda x: x[1]["hit"] + x[1]["miss"], reverse=True
    )
    for src, s in sorted_stats:
        src_total = s["hit"] + s["miss"]
        src_hit_rate = (s["hit"] / src_total * 100) if src_total > 0 else 0
        stats += f"- {src}: {src_total} total, {s['hit']} hit, {s['miss']} miss, hit rate: **{src_hit_rate:.2f}%**\n"
    return stats


def cache_get(key: str):
    if CACHE_ENABLED:
        src = key.split(":")[0] if ":" in key else "unknown"
        if src not in __STATS:
            __STATS[src] = {
                "hit": 0,
                "miss": 0,
            }
        try:
            cached = REDIS_CLIENT.get(key)
            if cached:
                __log(f"Hit: {key}")
                __STATS[src]["hit"] += 1
                return cached
            __warn(f"Miss: {key}")
            __STATS[src]["miss"] += 1
        except Exception as e:
            __error(f"Exception caught getting cache for key {key}: {e}")
    return None


def cache_set(key: str, value: str, ex=60):
    if CACHE_ENABLED:
        try:
            REDIS_CLIENT.set(key, value, ex=ex)
            __log(f"Set: {key} (expires in {ex} seconds)")
        except Exception as e:
            __error(f"Exception caught setting cache for key {key}: {e}")
