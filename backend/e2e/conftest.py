"""
Fixtures for e2e tests. Expects the environment from e2e/docker-compose.yml to be up
(see `make e2e`). Tests talk to the backend over HTTP, and to postgres directly for
setup (creating users/tokens etc) and assertions.
"""

import os

# must be set before importing anything from tpbackend, the db is configured on import
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "e2e")
os.environ.setdefault("DB_PASSWORD", "e2e")
os.environ.setdefault("OBLIVIONIS_DB", "oblivionis")
os.environ.setdefault("TIMEPLAYED_DB", "storage_v2")
os.environ.setdefault("CACHE_ENABLED", "false")

from typing import cast

import pytest
import requests
from playhouse.postgres_ext import PostgresqlExtDatabase

from tpbackend.storage import Game, Platform, User
from tpbackend.user.tokens import generate_token

DB_PORT = int(os.environ.get("E2E_DB_PORT", "55432"))
API_URL = os.environ.get("E2E_API_URL", "http://localhost:58000/api")

TIMEPLAYED_TABLES = [
    "history",
    "token",
    "liveactivity",
    "activity",
    "discordhistory",
    "game",
    '"user"',
    "platform",
]
OBLIVIONIS_TABLES = ["activity", "game", '"user"']


@pytest.fixture(scope="session")
def db():
    import tpbackend.storage as storage
    import tpbackend.oblivionis.storage as oblivionis_storage

    for d in (storage.db, oblivionis_storage.db):
        d.init(d.database, port=DB_PORT, **d.connect_params)
    oblivionis_storage.db.connect()
    storage.db.connect()
    yield storage.db, oblivionis_storage.db
    storage.db.close()
    oblivionis_storage.db.close()


@pytest.fixture(autouse=True)
def clean_db(db):
    """
    Every test starts with empty tables
    """
    tp_db, oblivionis_db = cast(tuple[PostgresqlExtDatabase, PostgresqlExtDatabase], db)
    tp_db.execute_sql(
        f"TRUNCATE {', '.join(TIMEPLAYED_TABLES)} RESTART IDENTITY CASCADE"
    )
    oblivionis_db.execute_sql(
        f"TRUNCATE {', '.join(OBLIVIONIS_TABLES)} RESTART IDENTITY CASCADE"
    )


class Api:
    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.session.get(API_URL + path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.session.post(API_URL + path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.session.put(API_URL + path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.session.patch(API_URL + path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.session.delete(API_URL + path, **kwargs)


@pytest.fixture
def api() -> Api:
    """
    Unauthenticated API client
    """
    return Api()


@pytest.fixture
def make_user():
    """
    Creates a user, returns (user, authenticated API client)
    """

    def _make(name: str = "testuser", **kwargs) -> tuple[User, Api]:
        user = cast(User, User.create(name=name, **kwargs))
        token = generate_token(user)
        return user, Api(token)

    return _make


@pytest.fixture
def make_game():
    def _make(name: str = "Test Game", **kwargs) -> Game:
        return cast(Game, Game.create(name=name, **kwargs))

    return _make


@pytest.fixture
def make_platform():
    def _make(abbreviation: str = "ps5", **kwargs) -> Platform:
        return cast(Platform, Platform.create(abbreviation=abbreviation, **kwargs))

    return _make
