"""Tests for AddGameCommand (!add_game)."""

import sys
from unittest.mock import patch

import pytest

import tpbackend.utils
from tpbackend.cmds.add_game import AddGameCommand


@pytest.fixture
def cmd():
    return AddGameCommand()


def test_new_user_without_activity_not_allowed(cmd, make_user, mock_api):
    mock_api.get_oldest_activity.return_value = None
    result = cmd.execute(make_user(id="user1"), "New Game")
    assert "not allowed" in result


def test_user_with_recent_activity_not_allowed(cmd, make_user, mock_api):
    from unittest.mock import MagicMock

    one_hour_ago_ts_ms = int((tpbackend.utils.now().timestamp() - 3600) * 1000)
    oldest = MagicMock()
    oldest.timestamp = one_hour_ago_ts_ms
    mock_api.get_oldest_activity.return_value = oldest

    result = cmd.execute(make_user(id="user1"), "New Game")
    assert "not allowed" in result


def test_admin_with_empty_name(cmd, make_admin_user):
    result = cmd.execute(make_admin_user(), "")
    assert "No game name provided" in result


def test_duplicate_game_rejected(cmd, make_admin_user, make_game):
    with patch("tpbackend.cmds.add_game.get_game_by_name_or_alias", return_value=make_game(1, "Existing Game")):
        result = cmd.execute(make_admin_user(), "Existing Game")
    assert "already exist" in result


def test_new_game_added(cmd, make_admin_user, make_game):
    with patch("tpbackend.cmds.add_game.get_game_by_name_or_alias", return_value=None):
        with patch(
            "tpbackend.cmds.add_game.get_game_by_name_or_alias_or_create",
            return_value=make_game(99, "Brand New Game"),
        ):
            result = cmd.execute(make_admin_user(), "Brand New Game")
    assert "✅" in result
    assert "Brand New Game" in result
