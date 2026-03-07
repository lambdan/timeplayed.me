"""Tests for AddActivityCommand (!add_activity)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.add_activity import AddActivityCommand
from tpbackend.storage.storage_v2 import Game, Platform


@pytest.fixture
def cmd():
    return AddActivityCommand()


def test_too_few_args(cmd, make_user):
    result = cmd.execute(make_user(), "onlyoneword")
    assert "Invalid syntax" in result


def test_game_not_found(cmd, make_user):
    with patch.object(Game, "get_or_none", return_value=None):
        with patch("tpbackend.cmds.add_activity.search_games", return_value=[]):
            result = cmd.execute(make_user(), "999 01:00:00")
    assert "Error" in result


def test_invalid_duration_format(cmd, make_user, make_game):
    with patch.object(Game, "get_or_none", return_value=make_game(1, "Castlevania")):
        result = cmd.execute(make_user(), "1 badformat")
    assert "Error" in result


def test_duration_too_long(cmd, make_user, make_game, mock_api):
    mock_api.get_activities.return_value.total = 0
    with patch.object(Game, "get_or_none", return_value=make_game(1, "Castlevania")):
        result = cmd.execute(make_user(), "1 17:00:00")
    assert "Error" in result


def test_successful_add(cmd, make_user, make_game, make_activity, make_platform, mock_api):
    mock_api.get_activities.return_value.total = 0
    saved = make_activity(1, seconds=3600)

    with patch.object(Game, "get_or_none", return_value=make_game(1, "Castlevania")):
        with patch("tpbackend.cmds.add_activity.last_platform_for_game", return_value=None):
            with patch.object(Platform, "get_by_id", return_value=make_platform()):
                with patch("tpbackend.cmds.add_activity.add_session", return_value=(saved, None)):
                    result = cmd.execute(make_user(), "1 01:00:00")

    assert "✅" in result
