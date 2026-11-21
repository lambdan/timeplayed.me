import threading
import time
import requests
import logging
import json

from tpbackend.cache import cache_get, cache_set
from tpbackend.globals import IGDB_CLIENT_ID, IGDB_CLIENT_SECRET
from tpbackend.igdb.rate_limit import RateLimiter
from tpbackend.utils2 import ts_to_dt

logger = logging.getLogger("IGDBClient")

# https://api-docs.igdb.com/#rate-limits
MAX_REQUESTS_PER_SECOND = 4
MAX_OPEN_REQUESTS = 8
# the limiter should keep us from getting 429s, but if we do anyway, wait and try again
MAX_TRIES = 3
# longer queries are cut in the logs
MAX_LOGGED_QUERY = 150


class IGDBClient:
    req_no = 0
    client_id = ""
    client_secret = ""
    token = ""
    expires = 0.0

    def __init__(self, client_id=IGDB_CLIENT_ID, client_secret=IGDB_CLIENT_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.expires = 0
        self.limiter = RateLimiter(MAX_REQUESTS_PER_SECOND, MAX_OPEN_REQUESTS)
        # requests come from several threads (sync routes, background tasks)
        self.auth_lock = threading.Lock()
        self.req_no_lock = threading.Lock()

    def _authenticate(self) -> bool:
        # one thread logs in, the others wait for it and use its token
        with self.auth_lock:
            return self.__authenticate()

    def __authenticate(self) -> bool:
        try:
            if not self.client_id or not self.client_secret:
                raise ValueError("IGDB client ID or secret not set")

            if self.token and time.time() < self.expires:
                return True

            logger.info(
                "Authenticating using %s... %s...",
                self.client_id[0:5],
                self.client_secret[0:5],
            )

            r = requests.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            )
            r.raise_for_status()
            data = r.json()
            self.token = data["access_token"]
            self.expires = float(time.time() + data["expires_in"])
            dt = ts_to_dt(self.expires)
            logger.info("Authenticated! Expires: %s", dt)
            return True
        except Exception as e:
            logger.error("Error during IGDB auth: %s", e)
            return False

    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def available(self) -> bool:
        return self.enabled() and self._authenticate()

    def request(self, url: str, query: str, cache_expiry=3600) -> str | None:
        if not self.enabled():
            return None
        # this request's number, self.req_no keeps counting with the other threads
        with self.req_no_lock:
            self.req_no += 1
            req_no = self.req_no

        def log(*args):
            logger.info(f"IGDB request #{req_no}: " + args[0], *args[1:])

        def error(*args):
            logger.error(f"IGDB request #{req_no}: " + args[0], *args[1:])

        # the queries are written over several lines, one is easier to read in the logs
        endpoint = url.rstrip("/").split("/")[-1]
        compact_query = " ".join(query.split())
        if len(compact_query) > MAX_LOGGED_QUERY:
            compact_query = compact_query[:MAX_LOGGED_QUERY] + "..."

        cache_key = f"igdb_request:{url}:{query}"
        cached = cache_get(cache_key)
        if cached:
            log("%s (cached) %s", endpoint, compact_query)
            return cached.decode("utf-8")  # type: ignore
        try:
            self._authenticate()
            log("%s %s", endpoint, compact_query)
            for attempt in range(1, MAX_TRIES + 1):
                with self.limiter.slot():
                    # timed in the slot, waiting for the rate limit doesn't count
                    started = time.monotonic()
                    r = requests.post(
                        url,
                        headers={
                            "Client-ID": self.client_id,
                            "Authorization": f"Bearer {self.token}",
                        },
                        data=query,
                    )
                if r.status_code != 429 or attempt == MAX_TRIES:
                    break
                error("Rate limited (429), trying again in a second")
                time.sleep(1)
            r.raise_for_status()
            json_str = r.text
            log(
                "%s %s, %d results, %d bytes, %.2fs",
                endpoint,
                r.status_code,
                len(json.loads(json_str)),
                len(json_str),
                time.monotonic() - started,
            )
            logger.debug("IGDB request #%d: response %s", req_no, json_str)
            cache_set(cache_key, json_str, ex=cache_expiry)
            return json_str
        except Exception as e:
            error("Error during IGDB request: %s", e)
            return None
