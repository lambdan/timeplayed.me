import time
import requests
import logging
import os
import json

from tpbackend.cache import cache_get, cache_set
from tpbackend.utils2 import ts_to_dt

logger = logging.getLogger("IGDBClient")
IGDB_CLIENT_ID = os.environ.get("IGDB_CLIENT_ID", "")
IGDB_CLIENT_SECRET = os.environ.get("IGDB_CLIENT_SECRET", "")


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

    def _authenticate(self) -> bool:
        try:
            if not self.client_id or not self.client_secret:
                raise ValueError("IGDB client ID or secret not set")

            if self.token and time.time() < self.expires:
                # logger.info("Auth still valid")
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

    def available(self) -> bool:
        return self._authenticate()

    def request(self, query: str, cache_expiry=3600) -> str | None:
        self.req_no += 1

        def log(*args):
            logger.info(f"IGDB request #{self.req_no}: " + args[0], *args[1:])

        def error(*args):
            logger.error(f"IGDB request #{self.req_no}: " + args[0], *args[1:])

        cache_key = f"igdb_request:{query}"
        cached = cache_get(cache_key)
        if cached:
            log("Cache hit for query: %s", query)
            return cached.decode("utf-8")  # type: ignore
        try:
            self._authenticate()
            log("Making query: %s", query)
            r = requests.post(
                "https://api.igdb.com/v4/games",
                headers={
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {self.token}",
                },
                data=query,
            )
            r.raise_for_status()
            json_str = r.text
            log("Response: %s %s", r.status_code, json_str)
            cache_set(cache_key, json_str, ex=cache_expiry)
            return json_str
        except Exception as e:
            error("Error during IGDB request: %s", e)
            return None
