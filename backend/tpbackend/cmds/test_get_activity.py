"""Tests for GetActivityCommand (!get_activity)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.get_activity import GetActivityCommand
from tpbackend.storage.storage_v2 import Activity, Game, Platform, User


@pytest.fixture
def cmd():
    return GetActivityCommand()


def test_activity_not_found(cmd, make_user):
    with patch.object(Activity, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "999")
    assert "Error" in result


def test_activity_found_shows_details(cmd, make_user, make_game, make_platform, make_activity):
    user = make_user()
    platform = make_platform(1, "switch", "Nintendo Switch")
    game = make_game(5, "Kirby")
    activity = make_activity(42, user=user, game=game, platform=platform, seconds=7200)

    with patch.object(Activity, "get_or_none", return_value=activity):
        with patch.object(User, "get_or_none", return_value=user):
            with patch.object(Game, "get_or_none", return_value=game):
                with patch.object(Platform, "get_or_none", return_value=platform):
                    result = cmd.execute(user, "42")

    assert "42" in result
    assert "Kirby" in result
    assert "testuser" in result
    assert "02:00:00" in result
