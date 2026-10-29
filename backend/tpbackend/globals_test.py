import importlib

import pytest

import tpbackend.globals

INTEGRATION_ENV = [
    "DISCORD_TOKEN",
    "SGDB_TOKEN",
    "IGDB_CLIENT_ID",
    "IGDB_CLIENT_SECRET",
    "OBLIVIONIS_DB",
]


@pytest.fixture
def load_globals(monkeypatch):
    """
    Reloads globals with only the given env set, since flags are read on import
    """

    def _load(**env):
        for k in INTEGRATION_ENV:
            monkeypatch.delenv(k, raising=False)
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        return importlib.reload(tpbackend.globals)

    yield _load
    monkeypatch.undo()
    importlib.reload(tpbackend.globals)


class TestIntegrationFlags:
    def test_all_disabled_by_default(self, load_globals):
        g = load_globals()
        assert not g.DISCORD_ENABLED
        assert not g.SGDB_ENABLED
        assert not g.IGDB_ENABLED
        assert not g.OBLIVIONIS_ENABLED

    def test_enabled_by_credentials(self, load_globals):
        g = load_globals(
            DISCORD_TOKEN="x",
            SGDB_TOKEN="x",
            IGDB_CLIENT_ID="x",
            IGDB_CLIENT_SECRET="x",
            OBLIVIONIS_DB="oblivionis",
        )
        assert g.DISCORD_ENABLED
        assert g.SGDB_ENABLED
        assert g.IGDB_ENABLED
        assert g.OBLIVIONIS_ENABLED

    def test_igdb_needs_both(self, load_globals):
        assert not load_globals(IGDB_CLIENT_ID="x").IGDB_ENABLED
        assert not load_globals(IGDB_CLIENT_SECRET="x").IGDB_ENABLED

    def test_empty_is_disabled(self, load_globals):
        g = load_globals(DISCORD_TOKEN="", SGDB_TOKEN="", OBLIVIONIS_DB="")
        assert not g.DISCORD_ENABLED
        assert not g.SGDB_ENABLED
        assert not g.OBLIVIONIS_ENABLED
