"""
Shared pytest configuration and fixtures for all tpbackend tests.

The environment variables and sys.modules mocking at module level runs as soon
as pytest imports this file — before any test module is collected — so every
test file can safely import tpbackend packages without a real database or
Discord connection.
"""

import datetime
import os
import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Environment & mock setup (must happen before any tpbackend import)
# ---------------------------------------------------------------------------

os.environ.setdefault("DB_NAME_TIMEPLAYED", "test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")

# Replace modules that have circular imports or external dependencies.
sys.modules["tpbackend.bot"] = MagicMock()
sys.modules["tpbackend.api"] = MagicMock()
sys.modules["tpbackend.steamgriddb"] = MagicMock()

# Import utils first to resolve the circular dependency between
# tpbackend.utils and tpbackend.storage.storage_v2.
import tpbackend.utils  # noqa: E402
from tpbackend.permissions import DEFAULT_PERMISSIONS, PERMISSION_ADMIN

from tpbackend.storage.storage_v2 import (  # noqa: E402
    Activity,
    Game,
    LiveActivity,
    Platform,
    User,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime.datetime(2025, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
_STARTED = datetime.datetime(2025, 6, 1, 11, 0, 0, tzinfo=datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures: mock API
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_mock_api():
    """Reset the mock tpbackend.api before every test to prevent state leakage."""
    sys.modules["tpbackend.api"].reset_mock()
    yield


@pytest.fixture
def mock_api():
    """Return the MagicMock that replaces tpbackend.api."""
    return sys.modules["tpbackend.api"]


# ---------------------------------------------------------------------------
# Fixtures: model factories
# ---------------------------------------------------------------------------


@pytest.fixture
def make_platform():
    """Factory fixture — returns a callable that creates mock Platform objects."""

    def _factory(id=1, abbreviation="win", name="Windows"):
        p = MagicMock(spec=Platform)
        p.id = id
        p.abbreviation = abbreviation
        p.name = name
        return p

    return _factory


@pytest.fixture
def make_game():
    """Factory fixture — returns a callable that creates mock Game objects."""

    def _factory(id=1, name="Test Game", aliases=None):
        g = MagicMock(spec=Game)
        g.id = id
        g.name = name
        g.aliases = aliases if aliases is not None else []
        return g

    return _factory


@pytest.fixture
def make_user(make_platform):
    """Factory fixture — returns a callable that creates mock User objects."""

    def _factory(
        id=1,
        discord_id="user1",
        name="testuser",
        permissions=DEFAULT_PERMISSIONS,
        default_platform=None,
        pc_platform="win",
    ):
        u = MagicMock(spec=User)
        u.id = id
        u.discord_id = discord_id
        u.name = name
        u.pc_platform = pc_platform
        u.permissions = permissions
        # make_platform is the factory callable injected by pytest; calling it
        # here creates a fresh, isolated Platform mock for each user so tests
        # are not accidentally coupled through a shared object.
        u.default_platform = (
            default_platform if default_platform is not None else make_platform()
        )
        # mock has_permission method
        u.has_permission = MagicMock(side_effect=lambda p: p in u.permissions)

        return u

    return _factory


@pytest.fixture
def make_admin_user(make_user):
    def _factory():
        permissions = DEFAULT_PERMISSIONS + [PERMISSION_ADMIN]
        return make_user(discord_id="admin123", name="admin", permissions=permissions)

    return _factory


@pytest.fixture
def make_activity(make_user, make_game, make_platform):
    """Factory fixture — returns a callable that creates mock Activity objects."""

    def _factory(
        id=1,
        user=None,
        game=None,
        platform=None,
        seconds=3600,
        timestamp=None,
        emulated=False,
    ):
        a = MagicMock(spec=Activity)
        a.id = id
        # Peewee's __str__ returns the primary key; replicate that so string
        # formatting in command output works as expected.
        a.__str__ = MagicMock(return_value=str(id))
        _user = user if user is not None else make_user()
        _game = game if game is not None else make_game()
        _platform = platform if platform is not None else make_platform()
        a.user = _user
        a.user_id = _user.id
        a.game = _game
        a.game_id = _game.id
        a.platform = _platform
        a.platform_id = _platform.id
        a.seconds = seconds
        a.timestamp = timestamp if timestamp is not None else _TS
        a.emulated = emulated
        return a

    return _factory


@pytest.fixture
def make_live_activity(make_user, make_game, make_platform):
    """Factory fixture — returns a callable that creates mock LiveActivity objects."""

    def _factory(user=None, game=None, platform=None, started=None):
        la = MagicMock(spec=LiveActivity)
        la.user = user if user is not None else make_user()
        la.game = game if game is not None else make_game()
        la.platform = platform if platform is not None else make_platform()
        la.started = started if started is not None else _STARTED
        return la

    return _factory


@pytest.fixture
def make_activity_queryset():
    """Factory fixture — returns a callable that creates a mock Peewee queryset."""

    def _factory(activities):
        qs = MagicMock()
        qs.where.return_value = qs
        qs.order_by.return_value = qs
        qs.limit.return_value = activities
        qs.__iter__ = MagicMock(return_value=iter(activities))
        qs.__len__ = MagicMock(return_value=len(activities))
        return qs

    return _factory
