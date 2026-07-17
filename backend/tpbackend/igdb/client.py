import time
import requests
import logging
import os
import json

from tpbackend.cache import cache_get, cache_set

logger = logging.getLogger("IGDBClient")
IGDB_CLIENT_ID = os.environ.get("IGDB_CLIENT_ID", "")
IGDB_CLIENT_SECRET = os.environ.get("IGDB_CLIENT_SECRET", "")


class IGDBClient:
    client_id = ""
    client_secret = ""
    token = ""
    expires = 0

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
                logger.info("Auth still valid")
                return True

            logger.info(
                "Authenticating using %s... %s...",
                self.client_id[0:5],
                self.client_secret[0:5],
            )

            logger.info("Authenticating with IGDB")
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
            self.expires = time.time() + data["expires_in"]
            logger.info("Authenticated! %s %s", self.token, self.expires)
            return True
        except Exception as e:
            logger.error("Error during IGDB auth: %s", e)
            return False

    def request(self, query: str, cache_expiry=3600) -> str | None:
        cache_key = f"igdb_request:{query}"
        cached = cache_get(cache_key)
        if cached:
            logger.info("Cache hit for query: %s", query)
            return cached.decode("utf-8")  # type: ignore
        try:
            self._authenticate()
            r = requests.post(
                "https://api.igdb.com/v4/games",
                headers={
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {self.token}",
                },
                data=query,
            )
            r.raise_for_status()
            json_str = json.dumps(r.json(), ensure_ascii=False)
            cache_set(cache_key, json_str, ex=cache_expiry)
            return json_str
        except Exception as e:
            logger.error("Error during IGDB request: %s", e)
            return None
