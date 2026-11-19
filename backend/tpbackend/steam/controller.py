"""
Covers from Steam. The store keeps the 600x900 library image under a hashed path for
newer apps, so the plain library_600x900.jpg url doesn't always work. The store browse
api has the real path, and doesn't need a key.
"""

import json
import logging

import requests

from tpbackend.cache import cache_get, cache_set

logger = logging.getLogger("steam")

ITEMS_URL = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1/"
ASSETS_URL = "https://shared.steamstatic.com/store_item_assets/"
CACHE_EXPIRY = 24 * 3600


def store_url(app_id: int) -> str:
    return f"https://store.steampowered.com/app/{app_id}"


def cover_url_from_item(item: dict) -> str | None:
    """the 600x900 library image of a store item, if it has one"""
    assets = item.get("assets") or {}
    url_format = assets.get("asset_url_format")
    filename = assets.get("library_capsule")
    if not url_format or not filename:
        return None
    return ASSETS_URL + url_format.replace("${FILENAME}", filename)


def __fetch_item(app_id: int) -> dict | None:
    """None if steam couldn't be asked, {} if it doesn't know the app"""
    input_json = {
        "ids": [{"appid": app_id}],
        "context": {"language": "english", "country_code": "US"},
        "data_request": {"include_assets": True},
    }
    try:
        r = requests.get(
            ITEMS_URL, params={"input_json": json.dumps(input_json)}, timeout=10
        )
        r.raise_for_status()
        items = r.json().get("response", {}).get("store_items", [])
    except Exception as e:
        logger.error("Error getting store item %d from Steam: %s", app_id, e)
        return None
    if not items:
        return {}
    return items[0]


def get_cover_url(app_id: int) -> str | None:
    key = f"steam_cover:{app_id}"
    cached = cache_get(key)
    if cached:
        # json so that "no cover" can be cached too
        return json.loads(cached.decode("utf-8"))  # type: ignore

    item = __fetch_item(app_id)
    if item is None:
        return None
    url = cover_url_from_item(item)
    cache_set(key, json.dumps(url), ex=CACHE_EXPIRY)
    return url
